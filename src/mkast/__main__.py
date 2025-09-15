#!/usr/bin/env python3
# ruff: noqa: E402,F401

from .mkast import generate_ast
from .cli import parse_args

def main():
    cfg, ast, emitter = parse_args()
    print(generate_ast(cfg, ast, emitter))

if __name__ == '__main__':
    main()