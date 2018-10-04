import ast
import functools
import inspect
import threading

from types import ModuleType
from typing import Any, Callable, Iterable, List, Dict, Tuple, Optional, TypeVar

from python_object_extractor.modules import get_module_by_name
from python_object_extractor.modules import is_project_module
from python_object_extractor.modules import is_stdlib_module
from python_object_extractor.modules import is_third_party_module
from python_object_extractor.references import make_name_from_object_reference
from python_object_extractor.references import ObjectReference


__caches = threading.local()
__caches.modules_imports = dict()


ObjectImport = TypeVar(
    name='ObjectImport',
    bound='ObjectImport',
)


class ObjectImport:
    __slots__ = ['object_reference', 'alias', 'substituted', 'access_chain', ]

    def __init__(
        self,
        object_reference: ObjectReference,
        alias: Optional[str] = None,
        substituted: Optional[ObjectImport] = None,
        access_chain: Optional[List[str]] = None,
    ):
        self.object_reference = object_reference
        self.alias = alias
        self.substituted = substituted
        self.access_chain = access_chain

    def __repr__(self) -> str:
        alias = f"'{self.alias}'" if self.alias else None
        return (
            f"<ObjectImport("
            f"object_reference='{repr(self.object_reference)}', "
            f"alias={alias})>"
        )

    def is_import_of_module(self) -> bool:
        return self.object_reference.object_name == self.object_reference.module_name

    def is_import_from_module(self) -> bool:
        return not self.is_import_of_module()

    def __str__(self) -> str:
        s = f"import {self.object_reference.object_name}"

        if self.is_import_from_module():
            s = f"from {self.object_reference.module_name} {s}"

        if self.alias and self.alias != self.object_reference.object_name:
            s = f"{s} as {self.alias}"

        return s

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: Any) -> bool:
        return (
                isinstance(other, ObjectImport)
            and self.object_reference == other.object_reference
            and self.alias == other.alias
        )


class ObjectImportsGroupped:
    __slots__ = ['stdlib', 'third_party', 'project', ]

    def __init__(
        self,
        stdlib: Optional[List[ObjectImport]] = None,
        third_party: Optional[List[ObjectImport]] = None,
        project: Optional[List[ObjectImport]] = None,
    ):
        self.stdlib = stdlib or None
        self.third_party = third_party or None
        self.project = project or None

    def __repr__(self) -> str:
        stdlib = (
                self.stdlib
            and repr([repr(x) for x in self.stdlib])
        )
        third_party = (
                self.third_party
            and repr([repr(x) for x in self.third_party])
        )
        project = (
                self.project
            and repr([repr(x) for x in self.project])
        )
        return (
            f"<ObjectImportsGroupped("
            f"stdlib={stdlib}, "
            f"third_party={third_party}, "
            f"project={project}"
            f")>"
        )

    def __str__(self) -> str:
        stdlib = (
                self.stdlib
            and repr([str(x) for x in self.stdlib])
        )
        third_party = (
                self.third_party
            and repr([str(x) for x in self.third_party])
        )
        project = (
                self.project
            and repr([str(x) for x in self.project])
        )
        return (
            f"ObjectImportsGroupped("
            f"stdlib={stdlib}, "
            f"third_party={third_party}, "
            f"project={project}"
            f")"
        )


def get_module_imports(module: ModuleType) -> List[ObjectImport]:
    results = __caches.modules_imports.get(module)

    if results is None:
        source = inspect.getsource(module)
        results = get_object_imports(source)
        __caches.modules_imports[module] = results

    return results


def get_object_imports(source: str) -> List[ObjectImport]:
    results = list()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                module_name = item.name
                reference = ObjectReference(
                    module_name=module_name,
                    object_name=module_name,
                )
                results.append(ObjectImport(
                    object_reference=reference,
                    alias=item.asname,
                ))
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            for item in node.names:
                reference = ObjectReference(
                    module_name=module_name,
                    object_name=item.name,
                )
                results.append(ObjectImport(
                    object_reference=reference,
                    alias=item.asname,
                ))

    return results


def group_imports_by_origin(
    imports: List[ObjectImport],
    project_path: str,
) -> ObjectImportsGroupped:
    module_names = {x.object_reference.module_name for x in imports}
    modules = {
        x: get_module_by_name(x)
        for x in module_names
    }
    imports, stdlib_imports = split_stdlib_imports(imports, modules)
    imports, third_party_imports = split_third_party_imports(imports, modules)
    _, project_imports = split_project_imports(imports, modules, project_path)
    return ObjectImportsGroupped(
        stdlib=stdlib_imports,
        third_party=third_party_imports,
        project=project_imports,
    )


def split_stdlib_imports(
    imports: List[ObjectImport],
    modules_map: Dict[str, ModuleType],
) -> Tuple[List[ObjectImport], List[ObjectImport]]:
    return split_imports(imports, modules_map, is_stdlib_module)


def split_third_party_imports(
    imports: List[ObjectImport],
    modules_map: Dict[str, ModuleType],
) -> Tuple[List[ObjectImport], List[ObjectImport]]:
    return split_imports(imports, modules_map, is_third_party_module)


def split_project_imports(
    imports: List[ObjectImport],
    modules_map: Dict[str, ModuleType],
    project_path: str,
) -> Tuple[List[ObjectImport], List[ObjectImport]]:
    condition = functools.partial(is_project_module, project_path=project_path)
    return split_imports(imports, modules_map, condition)


def split_imports(
    imports: List[ObjectImport],
    modules_map: Dict[str, ModuleType],
    condition: Callable[[ModuleType], bool],
) -> Tuple[List[ObjectImport], List[ObjectImport]]:
    selected = {
        x
        for x in imports
        if condition(modules_map[x.object_reference.module_name])
    }
    rejected = {
        x
        for x in imports
        if x not in selected
    }
    return (list(rejected), list(selected))


def group_aliases_by_references(
    references_to_aliases: Iterable[Tuple[ObjectReference, str]],
) -> Dict[ObjectReference, List[str]]:
    result = dict()

    for reference, alias in references_to_aliases:
        result.setdefault(reference, []).append(alias)

    return result


def group_references_by_aliases(
    references_to_aliases: Iterable[Tuple[ObjectReference, str]],
) -> Dict[str, List[ObjectReference]]:
    result = dict()

    for reference, alias in references_to_aliases:
        result.setdefault(alias, []).append(reference)

    return result


def resolve_import_conflicts(
    imports: Iterable[ObjectImport],
) -> List[ObjectImport]:
    references_to_alias_groupped = group_aliases_by_references([
        (x.object_reference, x.alias or x.object_reference.object_name)
        for x in imports
    ])
    references_to_aliases = [
        (
            reference,
            (
                alias_group[0]
                if len(alias_group) == 1
                else make_name_from_object_reference(reference)
            ),
        )
        for reference, alias_group in references_to_alias_groupped.items()
    ]
    aliases_to_references_groupped = group_references_by_aliases(references_to_aliases)
    results = []

    for alias, references in aliases_to_references_groupped.items():
        if len(references) == 1:
            results.append(ObjectImport(
                object_reference=references[0],
                alias=alias,
            ))
        else:
            results.extend([
                ObjectImport(
                    object_reference=reference,
                    alias=make_name_from_object_reference(reference),
                )
                for reference in references
            ])

    return results
