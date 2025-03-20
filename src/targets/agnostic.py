from src.domain import Emitter, NodeInfo, NodeKind
from src.util import println, csl, cslq

from collections.abc import Mapping
from itertools import chain


class AgnosticEmitter(Emitter):
    def intro(self) -> int:
        if self.cfg.namespace:
            print(f'namespace {self.cfg.namespace}')
        if self.cfg.root:
            print(f'root {self.cfg.root}')
        print()
        return 0

    def enter_node(
            self, lvl: int,
            parent: NodeInfo | None,
            node: NodeInfo,
            implements: Mapping[str, NodeKind],
            props: Mapping[str, str]):
        if reserved_props := props & self.cfg.common_props.keys():
            raise ValueError(f"reserved propety names in '{node.name}': {cslq(reserved_props)}")

        println(
            lvl,
            parent.name + ' >' if parent else '',
            node.kind.value, node.name,
            ': ' + csl(implements) if implements else ''
        )

        for pname, ptype in chain(props.items(), self.cfg.common_props.items()):
            println(lvl + 1, f'{pname} : {ptype}')
