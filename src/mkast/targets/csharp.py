from ..cfg import Modifier, ModifierKey
from ..domain import Config, Emitter, NodeInfo, NodeKind, camelize, pascalize, get_dont_touch_me
from ..util import println, csl, cslq, remove_prefix, sub

from collections.abc import Callable, Iterable, Mapping
from itertools import chain
import re

Keywords = {
    'abstract', 'as', 'base', 'bool', 'break', 'byte', 'case', 'catch', 'char', 'checked', 'class', 'const', 'continue',
    'decimal', 'default', 'delegate', 'do', 'double', 'else', 'enum', 'event', 'explicit', 'extern', 'false', 'finally', 'fixed',
    'float', 'for', 'foreach', 'goto', 'if', 'implicit', 'in', 'int', 'interface', 'internal', 'is', 'lock', 'long', 'namespace',
    'new', 'null', 'object', 'operator', 'out', 'override', 'params', 'private', 'protected', 'public', 'readonly', 'ref',
    'return', 'sbyte', 'sealed', 'short', 'sizeof', 'stackalloc', 'static', 'string', 'struct', 'switch', 'this', 'throw', 'true',
    'try', 'typeof', 'uint', 'ulong', 'unchecked', 'unsafe', 'ushort', 'using', 'virtual', 'void', 'volatile', 'while'
}


class CSharpEmitter(Emitter):
    def __init__(self, cfg: Config):
        super().__init__(cfg)

        self.usings = set(cfg.imports)

        if cfg.assert_:
            self.assert_ = cfg.assert_
        else:
            self.usings.add('System.Diagnostics')
            self.assert_ = 'Debug.Assert($1);'

        # $1.All($1 => $2)
        # $2: inner
        # $1: name
        self.modifiers: dict[ModifierKey, Modifier] = {
            '': cfg.modifiers.get('', Modifier()),
            '?': cfg.modifiers.get('?', Modifier(type='$1?', none_when='$1 is null')),
            '+': cfg.modifiers.get('+', Modifier(type='IReadOnlyList<$1>', must='$1.Count > 0', unwrap='$1.All($1 => $2)')),
            '*': cfg.modifiers.get('*', Modifier(type='IReadOnlyList<$1>', unwrap='$1.All($1 => $2)')),
        }

        self.node_kinds = {
            NodeKind.Product: cfg.product or 'public sealed class $1',
            NodeKind.Union: cfg.union or 'public interface $1'
        }

    def intro(self):
        if self.usings:
            for using in sorted(self.usings):
                print(f'using {using};')
            print()

        if self.cfg.namespace:
            print(f'namespace {self.cfg.namespace};')
            print()

        if not self.cfg.root:
            return 0

        print(sub(self.node_kinds[NodeKind.Union], 1, pascalize(self.cfg.root)))
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
            raise ValueError(f"reserved property names in '{node.name}': {cslq(reserved_props)}")

        props = dict(chain(self.cfg.common_props.items(), props.items()))

        need_explicit_constructor = any(map(self.requires_validation, props.values()))

        nk = self.node_kinds[node.kind]
        is_record = re.search(r'\brecord\b', nk) is not None
        println(lvl, sub(nk, 1, pascalize(node.name)), end='')

        # primary constructor arguments
        if node.kind is NodeKind.Product and props and not need_explicit_constructor:
            print(f'({csl(map(self.argument(pascalize if is_record else camel_ident), props.items()))})', end='')

        # base types list
        print(base_type_list((parent.name,) + tuple(implements.keys())
                             if parent and parent.kind is NodeKind.Union else
                             implements), end='')

        print()
        println(lvl, '{')

        lvl += 1
        if (not is_record or need_explicit_constructor) and node.kind is NodeKind.Product and props:
            if need_explicit_constructor:
                println(lvl, f'public {pascalize(node.name)}({csl(map(self.argument(camel_ident), props.items()))})')
                println(lvl, '{')
                for p in props.items():
                    self.put_assignment(lvl + 1, *p)
                println(lvl, '}')
                for p in props.items():
                    self.put_prop(lvl, node.name, *p, 'public')
            else:
                # primary constructor initializers
                for p in props.items():
                    self.put_prop(lvl, node.name, *p, 'public', True)

    def exit_node(self, lvl: int):
        println(lvl, '}')

    def conclusion(self):
        if self.cfg.root:
            print('}')

    def argument(self, name_transformer: Callable[[str], str]):
        return lambda prop: f'{self.real_type(prop[1])} {name_transformer(prop[0])}'

    def put_assignment(self, lvl: int, name: str, type: str):
        if val_expr := self.validation_expr(camel_ident(name), type):
            println(lvl, sub(self.assert_, 1, val_expr))
        println(lvl, f'{pascalize(name)} = {camel_ident(name)};')

    def put_prop(self, lvl: int, owner: str, name: str, type: str, access: str = '', put_init: bool = False):
        access = access + ' ' if access else ''
        init = ' = ' + camel_ident(name) + ';' if put_init else ''
        println(lvl, f'{access}{self.real_type(remove_prefix(owner + ".", type))} {pascalize(name)} {{ get; }}{init}')

    def real_type(self, type: str) -> str:
        if type[-1] not in self.modifiers:
            return pascalize(type)
        m = self.modifiers[type[-1]]
        return sub(m.type, 1, self.real_type(type[:-1]))

    def validation_expr(self, name: str, type: str):
        if type[-1] not in self.modifiers:
            return ''
        m = self.modifiers[type[-1]]

        # {none_when} || {must} && {unwrap}
        none_when = sub(m.none_when or '', 1, name)
        must = sub(m.must or '', 1, name)

        if '$2' in m.unwrap and (inner := self.validation_expr(name, type[:-1])):
            unwrap = sub(sub(m.unwrap, 1, name), 2, inner)
        else:
            name = sub(m.unwrap, 1, name)
            unwrap = self.validation_expr(name, type[:-1])

        r = ' && '.join(filter(None, (must, unwrap)))
        return ' || '.join(filter(None, (none_when, r)))

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
