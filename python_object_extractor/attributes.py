import ast

from typing import Any, List


class AttributesAccessChain:
    __slots__ = ['object_name', 'sequence']

    def __init__(
        self,
        object_name: str,
        sequence: List[str],
    ):
        self.object_name = object_name
        self.sequence = sequence

    def __repr__(self) -> str:
        return (
            f"<AttributesAccessChain("
            f"object_name='{self.object_name}', "
            f"sequence={self.sequence})>"
        )

    def __str__(self) -> str:
        access_chain = '.'.join(self.sequence)
        return f"{self.object_name}:{access_chain}"

    def __eq__(self, other: Any) -> bool:
        return (
                isinstance(other, AttributesAccessChain)
            and self.object_name == other.object_name
            and self.sequence == other.sequence
        )

    def __hash__(self) -> int:
        return hash(str(self))


def _traverse_attribute(node: ast.AST) -> List[str]:
    if isinstance(node, ast.Name):
        return [node.id, ]
    elif isinstance(node, ast.Attribute):
        symbols = _traverse_attribute(node.value)
        if symbols:
            symbols.append(node.attr)
            return symbols


def extract_attributes_access_chains(
    source: str,
) -> List[AttributesAccessChain]:
    tree = ast.parse(source)
    results = []

    for ast_node in ast.walk(tree):
        if isinstance(ast_node, ast.Attribute):
            chain = _traverse_attribute(ast_node)
            if chain:
                results.append(AttributesAccessChain(
                    object_name=chain[0],
                    sequence=chain[1:],
                ))

    return results
