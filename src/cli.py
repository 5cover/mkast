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

    keys = {'modifiers'}

    def add_key(key: str, *args, **kwargs):
        keys.add(key)
        argp.add_argument(*args, **kwargs, metavar=key)

    add_key('input', 'input', nargs='?', type=str, help='input file (default stdin)')
    add_key('target', '-t', '--target', help='target language')
    add_key('known_types', '--known-type', nargs='*', help='known type')
    add_key('common_props', '--common-prop', nargs='*', type=lambda x: x.split(':', 1), help="common property: 'name:type'")
    add_key('root', '--root', help='root node')
    add_key('namespace', '--namespace', help="namespace")

    a = argp.parse_args()
    cfg = {}

    if a.config:
        cfg = yaml.safe_load(a.config)

    for key in keys:
        attr = getattr(a, key, None)
        if attr is None:
            if key in key_defaults:
                cfg[key] = key_defaults[key]
            elif key not in cfg:
                argp.error(f"Missing option: '{key}'")
        else:
            cfg[key] = attr

    cfg = Config(
        ap.FileType()(cfg['input']),
        cfg['target'],
        set(cfg['known_types']),
        OrderedDict(cfg['common_props']),
        cfg['root'],
        cfg['namespace'],
        {k: Modifier() if v is None else Modifier(**v) for k, v in cfg['modifiers'].items()},
    )

    try:
        emitter = get_emitter(cfg)
    except KeyError:
        argp.error(f"unknown target '{cfg.target}'")

    return cfg, emitter
