#!/usr/bin/env python3
from src.astgen import generate_ast
from src.cli import parse_args

if __name__ == '__main__':
    cfg, emitter, ast = parse_args()
    generate_ast(cfg, emitter, ast)
