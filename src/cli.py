from src.astgen import get_emitter
from src.domain import Config, Modifier
from src.util import yaml_ordered_loader

from collections import ChainMap, OrderedDict
import argparse as ap
import yaml

default_config = {
    'target': 'agnostic',
    'known_types': set(),
    'common_props': OrderedDict(),
    'root': None,
    'namespace': None,
    'assertion': None,
    'modifiers': {},
    'imports': [],
}

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
    _ = argp.add_argument('--assertion', help='code for an assertion. $1 is replaced by the boolean expression to assert')
    _ = argp.add_argument('--imports', '--import', help='imports to add at the top of the file', nargs='*')

    cfg_cli = {k: v for k, v in vars(argp.parse_args()).items() if v is not None}

    if (kt := cfg_cli.get('known_types')) is not None:
        cfg_cli['known_types'] = set(kt),
    if (cp := cfg_cli.get('common_props')) is not None:
        cfg_cli['common_props'] = OrderedDict(cp),

    cfg_file = yaml.safe_load(cfg_cli.pop('config')) or {} if 'config' in cfg_cli else {}

    input: object = tuple(yaml.load_all(ap.FileType()(cfg_cli.get(
        'input') or cfg_file.get('input') or '-'), yaml_ordered_loader()))
    match len(input):
        case 2:
            cfg_input, input = input
        case 1:
            cfg_input, input = {}, input[0]
        case i:
            argp.error(f'input must contain 1 or 2 documents, not {i}')

    cfg_map = ChainMap(cfg_cli, cfg_input, cfg_file, default_config)
    if 'target' not in cfg_map:
        argp.error(f"key 'target' is required in configuration")
    
    cfg = Config(**cfg_map)
    if (emitter := get_emitter(cfg)) is None:
        argp.error(f"unknown target '{cfg.target}'")

    return cfg, emitter, input


def cfg_vals(values: dict):
    if 'modifiers' in values:
        values['modifiers'] = {k: Modifier(**v) for k, v in values['modifiers'].items()}
    return values


def prop(input: str) -> tuple[str, str]:
    s = input.split(':', 1)
    if len(s) < 2:
        raise ap.ArgumentTypeError(f"invalid property format: '{input}': missing separator")
    return s[0], s[1]
