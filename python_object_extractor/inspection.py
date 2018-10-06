import symtable

from types import ModuleType
from typing import Dict, List

from python_object_extractor.descriptors import ObjectDescriptor
from python_object_extractor.graph import sort_descriptors_topologically
from python_object_extractor.imports import get_module_imports
from python_object_extractor.imports import get_object_imports
from python_object_extractor.imports import group_imports_by_origin
from python_object_extractor.imports import group_references_by_aliases
from python_object_extractor.imports import ObjectImport
from python_object_extractor.imports import ObjectImportsGroupped
from python_object_extractor.modules import get_module_by_name
from python_object_extractor.references import ObjectReference
from python_object_extractor.sources import get_object_source
from python_object_extractor.substitutions import substitute_accesses_to_imported_modules
from python_object_extractor.symbols import contains_import_symbols
from python_object_extractor.symbols import exclude_import_symbols
from python_object_extractor.symbols import extract_symbols_from_source


def inspect_object_with_children(
    object_reference: ObjectReference,
    project_path: str,
) -> List[ObjectDescriptor]:
    references_to_descriptors = dict()
    _inspect_object_with_children(
        object_reference=object_reference,
        known_objects=references_to_descriptors,
        project_path=project_path,
    )
    return sort_descriptors_topologically(references_to_descriptors.values())


def _inspect_object_with_children(
    object_reference: ObjectReference,
    known_objects: Dict[ObjectReference, ObjectDescriptor],
    project_path: str,
) -> None:
    if object_reference in known_objects:
        return

    descriptor = inspect_object(
        project_path=project_path,
        object_reference=object_reference,
    )
    known_objects[object_reference] = descriptor

    if descriptor.global_imports and descriptor.global_imports.project:
        for item in descriptor.global_imports.project:
            _inspect_object_with_children(
                object_reference=item.object_reference,
                known_objects=known_objects,
                project_path=project_path,
            )


def inspect_object(
    project_path: str,
    object_reference: ObjectReference,
) -> ObjectDescriptor:
    module = get_module_by_name(object_reference.module_name)
    target = getattr(module, object_reference.object_name)
    source = get_object_source(
        module,
        target,
        object_reference.object_name,
    )
    symbols = extract_symbols_from_source(source)

    if contains_import_symbols(symbols):
        local_imports = inspect_local_imports(
            source=source,
            project_path=project_path,
        )
        symbols = exclude_import_symbols(symbols)
    else:
        local_imports = None

    if symbols:
        global_imports = inspect_global_imports(
            symbols=symbols,
            module=module,
            project_path=project_path,
        )
    else:
        global_imports = None

    if local_imports and local_imports.project:
        if not global_imports:
            global_imports = ObjectImportsGroupped()

        if not global_imports.project:
            global_imports.project = []

        global_imports.project.extend(local_imports.project)
        local_imports.project = None

    if global_imports and global_imports.project:
        global_imports.project = substitute_accesses_to_imported_modules(
            source=source,
            imports=global_imports.project,
        )

    return ObjectDescriptor(
        object_reference=object_reference,
        source=source,
        local_imports=local_imports,
        global_imports=global_imports,
    )


def inspect_local_imports(
    source: str,
    project_path: str,
) -> ObjectImportsGroupped:
    imports = get_object_imports(source)
    return group_imports_by_origin(imports, project_path)


def inspect_global_imports(
    symbols: List[symtable.Symbol],
    module: ModuleType,
    project_path: str,
) -> ObjectImportsGroupped:
    module_imports = get_module_imports(module)
    aliases_to_references_groupped = group_references_by_aliases([
        (
            x.object_reference,
            x.alias or x.object_reference.object_name,
        )
        for x in module_imports
    ])

    for alias, references in aliases_to_references_groupped.items():
        if len(references) > 1:
            for reference in references:
                try:
                    get_module_by_name(reference.module_name)
                except ModuleNotFoundError:
                    continue
                else:
                    references[:] = [reference, ]
                    break

    aliases_to_imports = {
        alias: ObjectImport(references[0], alias)
        for alias, references in aliases_to_references_groupped.items()
    }

    object_imports = list()

    for symbol in symbols:
        key = symbol.get_name()
        item = aliases_to_imports.get(key)

        is_sibling = item is None
        if is_sibling:
            reference = ObjectReference(
                module_name=module.__name__,
                object_name=key,
            )
            item = ObjectImport(
                object_reference=reference,
                alias=None,
            )

        object_imports.append(item)

    return group_imports_by_origin(object_imports, project_path)
