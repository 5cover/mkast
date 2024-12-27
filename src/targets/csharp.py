from src.domain import Config, Emitter, Modifier, ModifierKey, NodeInfo, NodeKind, camelize, pascalize, get_dont_touch_me
from src.util import println, csl, cslq, remove_prefix, sub_var

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
        super().__init__(cfg)

        self.usings = []

        if cfg.assertion:
            self.assertion = cfg.assertion
        else:
            self.usings.append('System.Diagnotics')
            self.assertion = 'Debug.Assert($1)'

        self.modifiers: dict[ModifierKey, Modifier] = {
            '?': cfg.modifiers.get('?', Modifier('$1?', none_when='$1 is null')),
            '1': cfg.modifiers.get('1', Modifier()),
            '+': cfg.modifiers.get('+', Modifier('IReadOnlyList<$1>', '$1.Count > 0', unwrap='$1.All($1 => $2)')),
            '*': cfg.modifiers.get('*', Modifier('IReadOnlyList<$1>', unwrap='$1.All($1 => $2)')),
        }

    def intro(self):
        if self.usings:
            for using in self.usings:
                print(f'using {using};')
            print()

        if self.cfg.namespace:
            print(f'namespace {self.cfg.namespace};')
            print()

        if not self.cfg.root:
            return 0

        print(f'public interface {pascalize(self.cfg.root)}')
        print('{')
        for p in self.cfg.common_props.items():
            self.put_prop(1, self.cfg.root, *p)
        return 1

    def enter_node(self,
                   lvl: int,
                   parent: NodeInfo | None,
                   node: NodeInfo,
                   implements: Mapping[str, NodeKind],
                   props: Mapping[str, str]):
        if reserved_props := props & self.cfg.common_props.keys():
            raise ValueError(f"reserved propety names in '{node.name}': {cslq(reserved_props)}")

        props = OrderedDict(chain(self.cfg.common_props.items(), props.items()))

        require_explicit_constructor = any((self.requires_validation(t) for t in props.values()))

        println(lvl, f'public {NodeKinds[node.kind]} {pascalize(node.name)}', end='')

        if node.kind is NodeKind.Class and props and not require_explicit_constructor:
            print(f'({csl(map(self.argument, props.items()))})', end='')

        print(base_type_list((parent.name,) + tuple(implements.keys())
                             if parent and parent.kind is NodeKind.Union else
                             implements))
        println(lvl, '{')

        lvl += 1
        if node.kind is NodeKind.Class and props:
            if require_explicit_constructor:
                println(lvl, f'public {pascalize(node.name)}({csl(map(self.argument, props.items()))})')
                println(lvl, '{')
                for p in props.items():
                    self.put_assignment(lvl + 1, *p)
                println(lvl, '}')
                for p in props.items():
                    self.put_prop(lvl, node.name, *p, 'public')
            else:
                for p in props.items():
                    self.put_prop(lvl, node.name, *p, 'public', True)

    def exit_node(self, lvl: int):
        println(lvl, '}')

    def conclusion(self):
        if self.cfg.root:
            print('}')

    def argument(self, prop: tuple[str, str]):
        return f'{self.real_type(prop[1])} {camel_ident(prop[0])}'

    def put_assignment(self, lvl: int, name: str, type: str):
        if vexpr := self.validation_expr(camel_ident(name), type):
            println(lvl, sub_var(self.assertion, 1, vexpr))
        println(lvl, f'{pascalize(name)} = {camel_ident(name)};')

    def put_prop(self, lvl: int, owner: str, name: str, type: str, access: str = '', put_init: bool = False):
        access = access + ' ' if access else ''
        init = ' = ' + camel_ident(name) + ';' if put_init else ''
        println(lvl, f'{access}{self.real_type(remove_prefix(owner + ".", type))} {pascalize(name)} {{ get; }}{init}')

    def real_type(self, type: str) -> str:
        if type[-1] not in self.modifiers:
            return pascalize(type)
        m = self.modifiers[type[-1]]
        return sub_var(m.type, 1, self.real_type(type[:-1]))

    def validation_expr(self, name: str, type: str):
        if type[-1] not in self.modifiers:
            return ''
        m = self.modifiers[type[-1]]

        # {none_when} || {must} && {unwrap}
        none_when = sub_var(m.none_when or '', 1, name)
        must = sub_var(m.must or '', 1, name)

        if '$2' in m.unwrap:
            # $1.All($1 => $2)
            # $2: inner
            # $1: name
            inner = self.validation_expr(name, type[:-1])
            unwrap = sub_var(sub_var(m.unwrap, 1, name), 2, inner)
        else:
            name = sub_var(m.unwrap, 1, name)
            unwrap = self.validation_expr(name, type[:-1])

        r = ' || '.join(filter(None, (none_when, must)))
        return ' && '.join(filter(None, (r, unwrap)))

    def requires_validation(self, type: str):
        validating_modifiers = {k for k, v in self.modifiers.items() if v.must}
        return any(c in validating_modifiers for c in type)


def base_type_list(bases: Iterable[str]):
    return ' : ' + csl(map(pascalize, bases)) if bases else ''


def camel_ident(name: str):
    if s := get_dont_touch_me(name):
        return s
    name = camelize(name)
    return '@' + name if name in Keywords else name
