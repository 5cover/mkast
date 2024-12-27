from src.domain import Config, Emitter, NodeInfo, NodeKind, camelize, pascalize, get_dont_touch_me
from src.util import println, csl, cslq, remove_prefix

from collections import OrderedDict
from collections.abc import Iterable, Mapping
from functools import cache
from itertools import chain

Keywords = {
    'abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch', 'char', 'checked', 'class', 'const', 'continue',
    'decimal', 'default', 'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit', 'extern', 'false', 'finally', 'fixed',
    'float', 'for', 'foreach', 'goto', 'if', 'implicit', 'in', 'int', 'interface', 'internal', 'is', 'lock', 'long', 'namespace',
    'new', 'null', 'object', 'operator', 'out', 'override', 'params', 'private', 'protected', 'public', 'readonly', 'ref',
    'return', 'sbyte', 'sealed', 'short', 'sizeof', 'stackalloc', 'static', 'string', 'struct', 'switch', 'this', 'throw', 'true',
    'try', 'typeof', 'uint', 'ulong', 'unchecked', 'unsafe', 'ushort', 'using', 'virtual', 'void', 'volatile', 'while'
}

NodeKinds = {NodeKind.Class: 'sealed class', NodeKind.Union: 'interface'}


class CSharpEmitter(Emitter):
    def __init__(self, cfg: Config):
        # self.type_opt, self.valid_opt = cfg.type_opt[0] or '$1?', cfg.type_opt[1]
        # self.type_plus, self.valid_opt = cfg.type_plus[0] or 'IReadOnlyList<$1>', cfg.type_plus[1] or '$1.Count > 0 && $1.All($2)'
        # self.type_star, self.valid_star = cfg.type_star[0] or 'IReadOnlyList<$1>', cfg.type_star[1] or '$1.All($2)'
        super().__init__(cfg)

    def intro(self):
        print('using System.Diagnostics;')
        print()
        if self.cfg.namespace:
            print(f'namespace {self.cfg.namespace};')
            print()
        print(f'public interface {pascalize(self.cfg.root)}')
        print('{')
        for p in self.cfg.common_props.items():
            put_prop(1, self.cfg.root, *p)
        print()
        return 1

    def enter_node(self,
                   lvl: int,
                   parent: NodeInfo,
                   node: NodeInfo,
                   implements: Mapping[str, NodeKind],
                   props: Mapping[str, str]):
        if reserved_props := props & self.cfg.common_props.keys():
            raise ValueError(f"reserved propety names in '{node.name}': {cslq(reserved_props)}")

        props = OrderedDict(chain(self.cfg.common_props.items(), props.items()))

        require_explicit_constructor = any((requires_validation(t) for t in props.values()))

        println(lvl, f'public {NodeKinds[node.kind]} {pascalize(node.name)}', end='')

        if node.kind is NodeKind.Class and props and not require_explicit_constructor:
            print(f'({csl(map(argument, props.items()))})', end='')

        print(base_type_list((parent.name,) + tuple(implements.keys())
                             if parent.kind is NodeKind.Union else
                             implements))
        println(lvl, '{')

        lvl += 1
        if node.kind is NodeKind.Class and props:
            if require_explicit_constructor:
                println(lvl, f'public {pascalize(node.name)}({csl(map(argument, props.items()))})')
                println(lvl, '{')
                for p in props.items():
                    put_assignment(lvl + 1, *p)
                println(lvl, '}')
                for p in props.items():
                    put_prop(lvl, node.name, *p, 'public')
            else:
                for p in props.items():
                    put_prop(lvl, node.name, *p, 'public', True)

    def exit_node(self, lvl: int):
        println(lvl, '}')

    def conclusion(self):
        print('}')


def argument(prop: tuple[str, str]):
    return f'{real_type(prop[1])} {camel_ident(prop[0])}'


def base_type_list(bases: Iterable[str]):
    return ' : ' + csl(map(pascalize, bases)) if bases else ''


def put_assignment(lvl: int, name: str, type: str):
    if vexpr := validation_expr(camel_ident(name), type):
        println(lvl, f'Debug.Assert({vexpr});')
    println(lvl, f'{pascalize(name)} = {camel_ident(name)};')


def put_prop(lvl: int, owner: str, name: str, type: str, access: str = '', put_init: bool = False):
    access = access + ' ' if access else ''
    init = ' = ' + camel_ident(name) + ';' if put_init else ''
    println(lvl, f'{access}{real_type(remove_prefix(owner + ".", type))} {pascalize(name)} {{ get; }}{init}')


@cache
def real_type(type: str) -> str:
    match type[-1]:
        case '?': return f'{real_type(type[:-1])}?'
        case '+': return f'IReadOnlyList<{real_type(type[:-1])}>'
        case '*': return f'IReadOnlyList<{real_type(type[:-1])}>'
        case _: return pascalize(type)


@cache
def validation_expr(name: str, type: str):
    match type[-1]:
        case '?':
            inner = validation_expr(name + '.Value', type[:-1])
            return f'!{name}.HasValue || {inner}' if inner else ''
        case '+':
            inner = validation_expr(name, type[:-1])
            return f'{name}.Count > 0' + (f' && {name}.All({name} => {inner})' if inner else '')
        case '*':
            inner = validation_expr(name, type[:-1])
            return f'{name}.All({name} => {inner})' if inner else ''
        case _: return ''


def requires_validation(type: str):
    return '+' in type


def sub_pattern(needle: str, pattern: str):
    return pattern.replace('$1', needle)


def camel_ident(name: str):
    if s := get_dont_touch_me(name):
        return s
    name = camelize(name)
    return '@' + name if name in Keywords else name
