from typing import Dict, Iterator

from python_object_extractor.descriptors import ObjectDescriptor
from python_object_extractor.references import ObjectReference


class ObjectsGraphNode:
    __slots__ = [
        'object_reference',
        'object_descriptor',
        'depth',
        'children',
    ]

    def __init__(
        self,
        object_reference: ObjectReference,
        object_descriptor: ObjectDescriptor,
        depth: int,
    ):
        self.object_reference = object_reference
        self.object_descriptor = object_descriptor
        self.depth = depth
        self.children = list()

    def __repr__(self) -> str:
        return (
            f"<ObjectsGraphNode("
            f"object_reference={repr(self.object_reference)}, "
            f"depth={self.depth}"
            f")>"
        )


def make_objects_graph(
    object_reference: ObjectReference,
    objects_references_to_descriptors: Dict[ObjectReference, ObjectDescriptor],
) -> ObjectsGraphNode:
    objects_references_to_nodes = dict()
    return _make_objects_graph(
        object_reference=object_reference,
        objects_references_to_descriptors=objects_references_to_descriptors,
        objects_references_to_nodes=objects_references_to_nodes,
        depth=0,
    )


def _make_objects_graph(
    object_reference: ObjectReference,
    objects_references_to_descriptors: Dict[ObjectReference, ObjectDescriptor],
    objects_references_to_nodes: Dict[ObjectReference, ObjectsGraphNode],
    depth: int,
) -> ObjectsGraphNode:
    node = objects_references_to_nodes.get(object_reference)

    if node:
        if node.depth < depth:
            node.depth = depth
        return node

    descriptor = objects_references_to_descriptors[object_reference]
    node = ObjectsGraphNode(
        object_reference=object_reference,
        object_descriptor=descriptor,
        depth=depth,
    )
    objects_references_to_nodes[object_reference] = node

    children_references = set()

    if descriptor.global_imports and descriptor.global_imports.project:
        for item in descriptor.global_imports.project:
            children_references.add(item.object_reference)

    node.children.extend([
        _make_objects_graph(
            object_reference=child_reference,
            objects_references_to_descriptors=objects_references_to_descriptors,
            objects_references_to_nodes=objects_references_to_nodes,
            depth=depth + 1,
        )
        for child_reference in sorted(children_references)
    ])

    return node


def _traverse_objects_graph(
    node: ObjectsGraphNode,
    depth: int,
) -> Iterator[ObjectsGraphNode]:
    if node.depth > depth:
        return

    yield node

    for child in node.children:
        yield from _traverse_objects_graph(
            node=child,
            depth=depth + 1,
        )


def traverse_objects_graph(
    root: ObjectsGraphNode,
) -> Iterator[ObjectsGraphNode]:
    yield from _traverse_objects_graph(root, 0)
