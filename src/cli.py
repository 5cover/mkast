from src.astgen import get_emitter
from src.domain import Config, Modifier

from collections import OrderedDict
import argparse as ap
import yaml


def parse_args():
    argp = ap.ArgumentParser('mkast', description="""
Generate an AST data structure from a language-agnostic description expressed in YAML.

Options take predecence over values in the config file, if provided.
""", formatter_class=ap.RawTextHelpFormatter)

    argp.add_argument('-c', '--config', type=ap.FileType(), help='config file')

    key_defaults = {
        'root': 'node',
        'known_types': set(),
        'common_props': {},
        'modifiers': {},
        'namespace': None,
    }

    keys = {'input', 'modifiers'}

    argp.add_argument('input', nargs='?', help='input file (default stdin)')

    def add_opt(key: str, *args, **kwargs):
        keys.add(key)
        argp.add_argument(*args, **kwargs, dest=key)
    add_opt('target', '-t', '--target', help='target language')
    add_opt('known_types', '--known-type', nargs='*', help='known type')
    add_opt('common_props', '--common-prop', nargs='*', type=prop, help="common property: 'name:type'")
    add_opt('root', '--root', help='root node')
    add_opt('namespace', '--namespace', help="namespace")

    a = argp.parse_args()
    config = {}

    if a.config:
        config = yaml.safe_load(a.config)

    for key in keys:
        attr = getattr(a, key, None)
        if attr is None:
            if key not in config:
                if key not in key_defaults:
                    argp.error(f"Missing option: '{key}'")
                config[key] = key_defaults[key]
        else:
            config[key] = attr

    cfg = Config(
        ap.FileType()(config['input']),
        config['target'],
        set(config['known_types']),
        OrderedDict(config['common_props']),
        config['root'],
        config['namespace'],
        {k: Modifier() if v is None else Modifier(**v) for k, v in config['modifiers'].items()},
    )

    try:
        emitter = get_emitter(cfg)
    except KeyError:
        argp.error(f"unknown target '{cfg.target}'")

    return cfg, emitter


def prop(input: str) -> tuple[str, str]:
    s = input.split(':', 1)
    if len(s) < 2:
        raise ap.ArgumentTypeError(f"invalid property format: '{input}': missing separator")
    return s[0], s[1]
