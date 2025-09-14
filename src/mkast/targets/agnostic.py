from ..domain import Emitter, NodeInfo, NodeKind
from ..util import concat, csl, cslq

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
            raise ValueError(f"reserved property names in '{node.name}': {cslq(reserved_props)}")

        self.write(
            concat(parent and parent.name + ' >',
                   node.kind.value, node.name,
                   implements and ': ' + csl(implements)),
            lvl
        )

        for propName, propType in chain(props.items(), self.cfg.common_props.items()):
            self.write(f'{propName} : {propType}', lvl + 1)
