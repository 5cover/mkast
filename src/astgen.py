from src.domain import Config, Emitter, NodeInfo, NodeKind, AstNode, AstUnionNode, is_do_not_touch
from src.util import csl, cslq
from src.targets.agnostic import AgnosticEmitter
from src.targets.csharp import CSharpEmitter

from collections import OrderedDict
from collections.abc import Iterable, Mapping, Set
from typing import TypeGuard

emitters = {
    'agnostic': AgnosticEmitter,
    'csharp': CSharpEmitter,
}


def get_emitter(cfg: Config):
    return emitters[cfg.target](cfg)


def generate_ast(cfg: Config, emitter: Emitter, ast: AstUnionNode):
    lvl = emitter.intro()
    for name, node in ast.items():
        walk(emitter, lvl, NodeInfo(cfg.root, NodeKind.Union), ast, name, node)
    emitter.conclusion()

# todo: instead of visiting on the fly, build a datastructure and revisit. this means we'll be able to query the properties and subnodes of a node when generating it, which will allow for smarter code generation (semi-colon body)

# invariant: reachable_nodes contains the current node


def walk(emitter: Emitter,
         lvl: int,
         parent: NodeInfo,
         reachable_nodes: AstUnionNode,
         name: str,
         node: AstNode):
    implements = OrderedDict(((k, NodeKind.Union) for k in in_unions(reachable_nodes, name) if k != parent.name))
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
            node = OrderedDict()

        subs = subnodes(node)
        if redefined_subs := subs & reachable_nodes.keys():
            raise ValueError(f"redefined subnodes in '{name}': {cslq(redefined_subs)}")
        props = OrderedDict((k, v) for k, v in node.items() if isinstance(v, str))
        if undef_type_props := tuple(f"'{k}' ('{v}')" for k, v in props.items() if not check_type(
                emitter.cfg.known_types, reachable_nodes, v)):
            raise ValueError(f"properties of undefined type in '{name}': {csl(undef_type_props)}")

        me = NodeInfo(name, NodeKind.Class)
        emitter.enter_node(lvl, parent, me, implements, props)
        for sub in subs.items():
            walk(emitter, lvl + 1, me, subs | reachable_nodes, *sub)
        emitter.exit_node(lvl)


def check_type(known_types: Set[str], reachable_nodes: AstUnionNode, ptype: str) -> bool:
    realtype = ptype.rstrip('*+?')
    if is_do_not_touch(ptype) or realtype in known_types:
        return True
    s = realtype.split('.', 1)
    if len(s) == 1:
        return s[0] in reachable_nodes.keys()
    first, others = s
    return check_type(
        known_types, reachable_nodes, first) and check_type(
        known_types, reachable_nodes | subnodes(reachable_nodes.get(first, None)),
        others)


def subnodes(node: AstNode) -> AstUnionNode:
    return OrderedDict() if node is None else OrderedDict((k, v) for k, v in node.items() if not isinstance(v, str))


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
