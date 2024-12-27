from src.domain import Emitter, NodeInfo, NodeKind
from src.util import println, csl, cslq

from collections.abc import Mapping
from itertools import chain


class AgnosticEmitter(Emitter):
    def enter_node(
            self, lvl: int,
            parent: NodeInfo,
            node: NodeInfo,
            implements: Mapping[str, NodeKind],
            props: Mapping[str, str]):
        if reserved_props := props & self.cfg.common_props.keys():
            raise ValueError(f"reserved propety names in '{node.name}': {cslq(reserved_props)}")

        base_list = ': ' + csl(implements) if implements else ''
        println(lvl, parent.name, '>', node.kind.value, node.name, base_list)
        for pname, ptype in chain(props.items(), self.cfg.common_props.items()):
            println(lvl + 1, f'{pname} : {ptype}')
