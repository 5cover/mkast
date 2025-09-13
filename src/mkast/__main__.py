# ruff: noqa: E402,F401

from .mkast import generate_ast
from .cli import parse_args

def main():
    cfg, emitter, ast = parse_args()
    generate_ast(cfg, emitter, ast)
