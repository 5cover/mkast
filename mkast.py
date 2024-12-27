#!/usr/bin/env python3
from src.astgen import generate_ast, get_emitter
from src.domain import AstNode
import src.cli as cli

from collections import OrderedDict
import yaml

if __name__ == '__main__':
    cfg, emitter = cli.parse_args()

    loader = yaml.SafeLoader
    loader.add_constructor(
        yaml.resolver.Resolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: OrderedDict(loader.construct_pairs(node)),
    )
    ast: OrderedDict[str, AstNode] = yaml.load(cfg.input_file, loader) or OrderedDict()

    generate_ast(cfg, emitter, ast)
