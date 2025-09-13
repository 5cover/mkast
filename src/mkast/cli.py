from typing import IO
import pydantic
from .cfg import load_cfg_file, merge_cfg
from .domain import AstUnionNode, Config, Emitter
from .mkast import get_emitter
import argparse as ap
import pathlib
import yaml
import sys
from .__version__ import __version__

# forward declare with strings
AstNodeModel = pydantic.RootModel[dict[str, "AstNodeModel | str"] | None]
AstUnionNodeModel = pydantic.RootModel[dict[str, AstNodeModel]]
# resolve forward refs
AstUnionNodeModel.model_rebuild()


def make_parser() -> ap.ArgumentParser:
    p = ap.ArgumentParser('mkast', description="""
Generate an AST data structure from a language-agnostic description expressed in YAML.

Options take precedence over values in the config file, if provided.
""", formatter_class=ap.RawTextHelpFormatter)
    _ = p.add_argument('-c', '--config', help='config file')
    _ = p.add_argument('input', nargs='?', type=str, help='input file (default stdin)')
    _ = p.add_argument('-t', '--target', help='target language')
    _ = p.add_argument('--known-type', nargs='*', type=set, help='known type', dest='known-types')
    _ = p.add_argument('--common-prop', nargs='*', type=prop, help="common property: 'name:type'", dest='common-props')
    _ = p.add_argument('--root', help='root node')
    _ = p.add_argument('--namespace', help='namespace')
    _ = p.add_argument('--assert', help='Expands to an assertion statement. $1 is replaced by the boolean expression to assert')
    _ = p.add_argument('--union', help='Expands to the declaration of an union node. $1 is replaced by the name of the node.')
    _ = p.add_argument('--product', help='Expands to the declaration of an product node. $1 is replaced by the name of the node.')
    _ = p.add_argument('--imports', '--import', help='imports to add at the top of the file', nargs='*')
    _ = p.add_argument('--dump', action='store_true', help='Dump config and input and exit')
    _ = p.add_argument('--version', action='store_true', help='Show version exit')
    return p

def prop(input: str) -> tuple[str, str]:
    s = input.split(':', 1)
    if len(s) < 2:
        raise ap.ArgumentTypeError(f"invalid property format: '{input}': missing separator")
    return s[0], s[1]


def config_from_args(args: ap.Namespace) -> Config:
    return Config.model_validate({k: v for k, v in vars(args).items() if v is not None})


def resolve_config(cfg: Config, filename: pathlib.Path) -> Config:
    visited = set()
    cfgF = None
    while not cfgF or (cfgF.extends and (filename := (filename.parent / cfgF.extends).resolve()) not in visited):
        visited.add(filename)
        cfgF = load_cfg_file(filename)
        cfg = merge_cfg(cfg, cfgF)
    return cfg


def load_input(stream: IO) -> tuple[Config | None, AstUnionNode]:
    docs = tuple(yaml.safe_load_all(stream))
    match len(docs):
        case 2:
            return Config.model_validate(docs[0]), AstUnionNodeModel(docs[1]).model_dump()
        case 1:
            return None, AstUnionNodeModel(docs[0]).model_dump()
        case i:
            raise ValueError(f"expected 1 or 2 documents, not {i}")


def parse_args() -> tuple[Config, Emitter, AstUnionNode]:
    p = make_parser()
    args = p.parse_args()
    if args.version:
        print(f'mkast {__version__}')
        exit()
    cfg = config_from_args(args)
    cfg = resolve_config(cfg, pathlib.Path(args.config))
    try:
        input_cfg, input = load_input(ap.FileType()(str(cfg.input) if cfg.input else '-'))
    except pydantic.ValidationError as e:
        p.error(f"invalid input{f" '{cfg.input}'" if cfg.input else ''}: {e}")
    except ValueError as e:
        p.error(' '.join(e.args))
    if input_cfg:
        cfg = merge_cfg(cfg, input_cfg)
    if args.dump:
        print('CONFIG:', cfg)
        print('INPUT:', input)
        exit()
    return cfg, get_emitter(cfg) or p.error(f"unknown target '{cfg.target}'"), input
