from typing import Set, Optional

from python_object_extractor.imports import ObjectImport
from python_object_extractor.imports import ObjectImportsGroupped
from python_object_extractor.references import ObjectReference


class ObjectDescriptor:
    __slots__ = [
        'object_reference',
        'source',
        'local_imports',
        'global_imports',
    ]

    def __init__(
        self,
        object_reference: ObjectReference,
        source: str,
        local_imports: Optional[ObjectImportsGroupped] = None,
        global_imports: Optional[ObjectImportsGroupped] = None,
    ):
        self.object_reference = object_reference
        self.source = source
        self.local_imports = local_imports
        self.global_imports = global_imports

    def __repr__(self) -> str:
        return (
            f"<ObjectDescriptor("
            f"object_reference={repr(self.object_reference)}"
            f")>"
        )

    def gather_imports(self) -> Set[ObjectImport]:
        results = set()

        if self.local_imports:
            results |= self._gather_imports_from_group(self.local_imports)

        if self.global_imports:
            results |= self._gather_imports_from_group(self.global_imports)

        return results

    def _gather_imports_from_group(
        self,
        imports_group: ObjectImportsGroupped,
    ) -> Set[ObjectImport]:
        results = set()

        if imports_group.stdlib:
            results |= set(imports_group.stdlib)

        if imports_group.third_party:
            results |= set(imports_group.third_party)

        if imports_group.project:
            results |= set(imports_group.project)

        return results
