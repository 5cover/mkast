from .domain import Config, Emitter, NodeInfo, NodeKind, AstNode, AstUnionNode, is_do_not_touch
from .util import csl, cslq
from .targets.agnostic import AgnosticEmitter
from .targets.csharp import CSharpEmitter

from collections.abc import Iterable, Mapping, Set
from typing import TypeGuard

emitters = {
    'agnostic': AgnosticEmitter,
    'csharp': CSharpEmitter,
}


def get_emitter(cfg: Config) -> Emitter | None:
    cls = emitters.get(cfg.target, None)
    return None if cls is None else cls(cfg)


def generate_ast(cfg: Config, emitter: Emitter, ast: AstUnionNode):
    root_node_info = None if cfg.root is None else NodeInfo(cfg.root, NodeKind.Union)
    lvl = emitter.intro()
    for name, node in ast.items():
        walk(emitter, lvl, root_node_info, ast, name, node)
    emitter.conclusion()


def walk(emitter: Emitter,
         lvl: int,
         parent: NodeInfo | None,
         reachable_nodes: AstUnionNode,
         name: str,
         node: AstNode):
    assert reachable_nodes[name] is node, 'invariant: reachable_nodes contains the current node'

    implements = {k: NodeKind.Union for k in in_unions(reachable_nodes, name) if parent is None or k != parent.name}
    if node_is_union(node):
        if redefined_nodes := {k for k in node & reachable_nodes.keys() if node[k] is not None}:
            raise ValueError(f"redefined nodes in '{name}': {cslq(redefined_nodes)}")

        me = NodeInfo(name, NodeKind.Union)
        emitter.enter_node(lvl, parent, me, implements, {})
        for sub in ((k, v) for k, v in node.items() if k not in reachable_nodes.keys()):
            walk(emitter, lvl + 1, me, node | reachable_nodes, *sub)
        emitter.exit_node(lvl)
    else:
        if node is None:
            node = {}

        subs = subnodes(node)
        if redefined_subs := subs & reachable_nodes.keys():
            raise ValueError(f"redefined subnodes in '{name}': {cslq(redefined_subs)}")
        props = {k: v for k, v in node.items() if isinstance(v, str)}
        if undef_type_props := tuple(f"'{k}' ('{v}')" for k, v in props.items() if not check_type(
                emitter.cfg.known_types, reachable_nodes, v)):
            raise ValueError(f"properties of undefined type in '{name}': {csl(undef_type_props)}")

        me = NodeInfo(name, NodeKind.Product)
        emitter.enter_node(lvl, parent, me, implements, props)
        for sub in subs.items():
            walk(emitter, lvl + 1, me, subs | reachable_nodes, *sub)
        emitter.exit_node(lvl)


def check_type(known_types: Set[str], reachable_nodes: AstUnionNode, ptype: str) -> bool:
    real_type = ptype.rstrip('*+?')
    if is_do_not_touch(ptype) or real_type in known_types:
        return True
    s = real_type.split('.', 1)
    if len(s) == 1:
        return s[0] in reachable_nodes.keys()
    first, others = s
    return check_type(
        known_types, reachable_nodes, first) and check_type(
        known_types, reachable_nodes | subnodes(reachable_nodes.get(first, None)),
        others)


def subnodes(node: AstNode) -> AstUnionNode:
    return {} if node is None else {k: v for k, v in node.items() if not isinstance(v, str)}


def in_unions(reachable_nodes: Mapping[str, AstNode], name: str) -> Iterable[str]:
    """ Returns the names of each union this node is in"""
    for k, v in reachable_nodes.items():
        if node_is_union(v):
            if name in v:
                yield k
        else:
            yield from in_unions(subnodes(v), name)


def node_is_union(node: AstNode) -> TypeGuard[AstUnionNode]:
    return node is not None and not any(isinstance(v, str) for v in node.values())
