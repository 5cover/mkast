# ruff: noqa: E402,F401

from .mkast import generate_ast
from .cli import parse_args

def main():
    cfg, ast, emitter = parse_args()
    generate_ast(cfg, ast, emitter)
