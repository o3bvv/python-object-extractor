import operator

from typing import Iterable, List

from python_object_extractor.descriptors import ObjectDescriptor
from python_object_extractor.references import ObjectReference


class GraphNode:
    __slots__ = [
        'descriptor',
        'incoming_edges',
    ]

    def __init__(
        self,
        descriptor: ObjectDescriptor,
        incoming_edges: List[ObjectReference],
    ):
        self.descriptor = descriptor
        self.incoming_edges = incoming_edges


def sort_descriptors_topologically(
    descriptors: Iterable[ObjectDescriptor]
) -> List[ObjectDescriptor]:
    nodes = [
        GraphNode(
            descriptor=descriptor,
            incoming_edges=(
                (
                        descriptor.global_imports
                    and descriptor.global_imports.project
                    and set([
                        x.object_reference
                        for x in descriptor.global_imports.project
                    ])
                )
                or []
            ),
        )
        for descriptor in descriptors
    ]
    sorting_key = operator.attrgetter('descriptor.object_reference')

    leafs = [node for node in nodes if not node.incoming_edges]
    leafs = list(sorted(leafs, key=sorting_key))
    nodes = [x for x in nodes if x not in leafs]

    results = []

    while leafs:
        leaf = leafs.pop()
        results.append(leaf.descriptor)

        for node in nodes.copy():
            if leaf.descriptor.object_reference in node.incoming_edges:
                node.incoming_edges.remove(leaf.descriptor.object_reference)
                if not node.incoming_edges:
                    leafs.append(node)
                    nodes.remove(node)

    return results
