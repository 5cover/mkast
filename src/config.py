from collections import OrderedDict
from collections.abc import Set
from dataclasses import dataclass
import argparse as ap
from typing import IO

import yaml


@dataclass
class Config:
    input_file: IO
    root: str
    known_types: Set[str]
    common_props: OrderedDict[str, str]
    target: str
    namespace: str


def add_key(keys: dict, argp: ap.ArgumentParser, key: str, *args, **kwargs):
    keys[key] = argp.add_argument(*args, **kwargs, metavar=key)


def parse_args():
    argp = ap.ArgumentParser('mkast')

    argp.add_argument('-c', '--config', type=ap.FileType(), help='config file')
    keys = {}
    add_key(keys, argp, 'input', 'input', nargs='?', type=str, help='input file (default stdin)')
    add_key(keys, argp, 'root', '--root', help='override the config root node')
    add_key(keys, argp, 'target', '--target', help='target language')
    add_key(keys, argp, 'known_types', '--known-type', nargs='*', help='known type')
    add_key(keys, argp, 'namespace', '--namespace', help="namespace'")
    add_key(keys, argp, 'common_props', '--common-prop', nargs='*',
            type=lambda x: x.split(':', 1), help="common property: 'name:type'")
    a = argp.parse_args()

    config = {}

    key_defaults = {
        'known_types': set(),
        'common_props': {},
    }

    if a.config:
        config = yaml.safe_load(a.config)

    for key in keys:
        attr = getattr(a, key, None)
        if attr is None:
            if key in key_defaults:
                config[key] = key_defaults[key]
            elif key not in config:
                argp.error(f"Missing option: '{key}'")
        else:
            config[key] = attr

    return Config(
        ap.FileType()(config['input']),
        config['root'],
        set(config['known_types']),
        OrderedDict(config['common_props']),
        config['target'],
        config['namespace'],
    )
