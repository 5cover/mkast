from typing import cast
from src.astgen import get_emitter
from src.domain import AstUnionNode, Config, Modifier
from src.util import yaml_ordered_loader

from collections import ChainMap, OrderedDict
import argparse as ap
import yaml

def postprocess_loaded_cfg(cfg: dict[str, object]):
    if 'assert' in cfg:
        cfg['assert_'] = cfg.pop('assert')
    return cfg

default_config = postprocess_loaded_cfg({
    'target': 'agnostic',
    'known_types': set(),
    'common_props': OrderedDict(),
    'root': None,
    'namespace': None,
    'assert': None,
    'union': None,
    'product': None,
    'imports': [],
    'modifiers': {},
})

def parse_args():
    argp = ap.ArgumentParser('mkast', description="""
Generate an AST data structure from a language-agnostic description expressed in YAML.

Options take predecence over values in the config file, if provided.
""", formatter_class=ap.RawTextHelpFormatter)
    _ = argp.add_argument('-c', '--config', type=ap.FileType(), help='config file')
    _ = argp.add_argument('input', nargs='?', type=str, help='input file (default stdin)')
    _ = argp.add_argument('-t', '--target', help='target language')
    _ = argp.add_argument('--known-types', '--known-type', nargs='*', type=set, help='known type')
    _ = argp.add_argument('--common-props', '--common-prop', nargs='*', type=prop, help="common property: 'name:type'")
    _ = argp.add_argument('--root', help='root node')
    _ = argp.add_argument('--namespace', help='namespace')
    _ = argp.add_argument('--assert', help='Expands to an assertion statement. $1 is replaced by the boolean expression to assert')
    _ = argp.add_argument('--union', help='Expands to the declaration of an union node. $1 is replaced by the name of the node.')
    _ = argp.add_argument('--product', help='Expands to the declaration of an product node. $1 is replaced by the name of the node.')
    _ = argp.add_argument('--imports', '--import', help='imports to add at the top of the file', nargs='*')

    cfg_cli = {k: v for k, v in vars(argp.parse_args()).items() if v is not None}

    if (kt := cfg_cli.get('known_types')) is not None:
        cfg_cli['known_types'] = set(kt),
    if (cp := cfg_cli.get('common_props')) is not None:
        cfg_cli['common_props'] = OrderedDict(cp),

    cfg_file = postprocess_loaded_cfg(yaml.safe_load(cfg_cli.pop('config')) or {} if 'config' in cfg_cli else {})

    input_filename = cfg_cli.get('input') or str(cfg_file.get('input')) or '-'

    input = tuple(yaml.load_all(ap.FileType()(input_filename), yaml_ordered_loader()))
    match len(input):
        case 2:
            cfg_input, input = input
            postprocess_loaded_cfg(cfg_input)
        case 1:
            cfg_input, input = {}, input[0]
        case i:
            argp.error(f'input must contain 1 or 2 documents, not {i}')

    cfg_map = ChainMap(cfg_cli, cfg_input, cfg_file, default_config)
    if 'target' not in cfg_map:
        argp.error(f"key 'target' is required in configuration")

    if 'modifiers' in cfg_map:
        cfg_map['modifiers'] = {k: Modifier(**v) for k, v in cfg_map['modifiers'].items()}

    cfg = Config(**cfg_map)
    if (emitter := get_emitter(cfg)) is None:
        argp.error(f"unknown target '{cfg.target}'")

    return cfg, emitter, cast(AstUnionNode, input)

def prop(input: str) -> tuple[str, str]:
    s = input.split(':', 1)
    if len(s) < 2:
        raise ap.ArgumentTypeError(f"invalid property format: '{input}': missing separator")
    return s[0], s[1]
