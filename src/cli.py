from src.astgen import get_emitter
from src.domain import Config, Modifier
from src.util import yaml_ordered_loader

from collections import OrderedDict
import argparse as ap
import yaml


default_config = Config(
    None,
    input=None,
    target='agnostic',
    known_types=set(),
    common_props=OrderedDict(),
    root=None,
    namespace=None,
    assertion=None,
    modifiers={},
)

def parse_args():
    argp = ap.ArgumentParser('mkast', description="""
Generate an AST data structure from a language-agnostic description expressed in YAML.

Options take predecence over values in the config file, if provided.
""", formatter_class=ap.RawTextHelpFormatter)
    argp.add_argument('-c', '--config', type=ap.FileType(), help='config file')
    argp.add_argument('input', nargs='?', type=str, help='input file (default stdin)')
    argp.add_argument('-t', '--target', help='target language')
    argp.add_argument('--known-type', dest='known_types', nargs='*', type=set, help='known type')
    argp.add_argument('--common-prop', dest='common_props', nargs='*', type=prop, help="common property: 'name:type'")
    argp.add_argument('--root', help='root node')
    argp.add_argument('--namespace', help='namespace')
    argp.add_argument('--assertion', help='code for an assertion. $1 is replaced by the boolean expression to assert')
    cli_c = dict(filter(lambda kv: kv[1] is not None, vars(argp.parse_args()).items()))
    if 'known_types' in cli_c:
        cli_c['known_types'] = set(cli_c['known_types']),
    if 'common_props' in cli_c:
        cli_c['common_props'] = OrderedDict(cli_c['common_props']),


    file_c = yaml.safe_load(cli_c.pop('config')) or {} if 'config' in cli_c else {}

    input = tuple(yaml.load_all(ap.FileType()(cli_c.get('input') or file_c.get('input') or '-'), yaml_ordered_loader()))
    match len(input):
        case 2:
            input_c, input = input
        case 1:
            input_c, input = {}, input[0]
        case i:
            argp.error(f'input must contain 1 or 2 documents, not {i}')
        
    cfg = Config(Config(Config(default_config, **config_values(input_c)), **config_values(file_c)), **config_values(cli_c))

    if (emitter := get_emitter(cfg)) is None:
        argp.error(f"unknown target '{cfg.target}'")

    return cfg, emitter, input

def config_values(values: dict):
    if 'modifiers' in values:
       values['modifiers'] = {k: Modifier(**v) for k, v in values['modifiers'].items()}
    return values

def prop(input: str) -> tuple[str, str]:
    s = input.split(':', 1)
    if len(s) < 2:
        raise ap.ArgumentTypeError(f"invalid property format: '{input}': missing separator")
    return s[0], s[1]
