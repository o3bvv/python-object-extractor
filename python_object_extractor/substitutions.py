import inspect

from typing import Dict, List, Set, Optional, Iterable

from python_object_extractor.attributes import AttributesAccessChain
from python_object_extractor.attributes import extract_attributes_access_chains
from python_object_extractor.exceptions import PythonObjectExtractorException
from python_object_extractor.imports import ObjectImport
from python_object_extractor.imports import ObjectImportsGroupped
from python_object_extractor.modules import get_module_by_name
from python_object_extractor.references import ObjectReference


class NoAccessedModuleObjects(PythonObjectExtractorException):

    def __init__(
        self,
        imported_module_name: str,
        source: str,
    ):
        super().__init__(
            f"object refers to imported module but does not access any of its "
            f"members, imported module: '{imported_module_name}', "
            f"object source:\n{source}"
        )


def _extract_imported_objects_access_chains(
    source: str,
    imported_objects_names: Set[str],
) -> List[AttributesAccessChain]:
    access_chains = extract_attributes_access_chains(source)
    return [
        x for x in access_chains
        if x.object_name in imported_objects_names
    ]


def _find_first_non_module_index(
    module_name: str,
    object_name: str,
    access_chain: List[str],
) -> Optional[int]:
    if module_name == object_name:
        object_full_name = module_name
    else:
        object_full_name = f"{module_name}.{object_name}"
        module = get_module_by_name(module_name)

        try:
            the_object = getattr(module, object_name)
        except AttributeError:
            the_object = get_module_by_name(object_full_name)

        if not inspect.ismodule(the_object):
            return 0

    if not access_chain:
        return

    subindex = _find_first_non_module_index(
        object_full_name,
        access_chain[0],
        access_chain[1:],
    )

    if subindex is not None:
        return subindex + 1


def substitute_accesses_to_imported_modules(
    source: str,
    imports: List[ObjectImport],
) -> List[ObjectImport]:
    alias_to_imports = {
        (x.alias or x.object_reference.object_name): x
        for x in imports
    }
    access_chains = _extract_imported_objects_access_chains(
        source=source,
        imported_objects_names=set(alias_to_imports.keys()),
    )
    results = set(imports)

    for access_chain in access_chains:
        original_import = alias_to_imports[access_chain.object_name]
        new_reference = maybe_make_import_substitution(
            imported_module_name=original_import.object_reference.module_name,
            imported_object_name=original_import.object_reference.object_name,
            access_chain=access_chain.sequence,
            source=source,
        )
        if new_reference:
            original_import.access_chain = access_chain.sequence
            results.remove(original_import)
            results.add(ObjectImport(
                object_reference=new_reference,
                alias=None,
                substituted=original_import,
            ))

    return list(results)


def maybe_make_import_substitution(
    imported_module_name: str,
    imported_object_name: str,
    access_chain: List[str],
    source: str,
) -> Optional[ObjectReference]:
    idx = _find_first_non_module_index(
        module_name=imported_module_name,
        object_name=imported_object_name,
        access_chain=access_chain,
    )

    if idx is None:
        imported_module_name = "{}.{}.{}".format(
            imported_module_name,
            imported_object_name,
            ".".join(access_chain),
        )
        raise NoAccessedModuleObjects(imported_module_name, source)

    if idx == 0:
        return

    idx -= 1
    new_subpath = access_chain[:idx]
    new_module_name_path = [imported_module_name, ]

    if imported_module_name != imported_object_name:
        new_module_name_path.append(imported_object_name)

    new_module_name_path.extend(new_subpath)
    new_module_name = ".".join(new_module_name_path)
    new_object_name = access_chain[idx]

    return ObjectReference(
        module_name=new_module_name,
        object_name=new_object_name,
    )


def substitute_aliases_of_imports(
    imports: Iterable[ObjectImport],
    references_to_aliases: Dict[ObjectReference, str],
) -> List[ObjectImport]:
    results = []

    for imported_object in imports:
        imported_alias = (
               imported_object.alias
            or imported_object.object_reference.object_name
        )
        substituted_alias = references_to_aliases.get(
            imported_object.object_reference,
        )
        if substituted_alias and imported_alias != substituted_alias:
            imported_object = ObjectImport(
                object_reference=imported_object.object_reference,
                alias=substituted_alias,
                substituted=imported_object,
            )
        results.append(imported_object)

    return results


def substitute_aliases_of_groupped_imports(
    groupped_imports: List[ObjectImportsGroupped],
    references_to_aliases: Dict[ObjectReference, str],
) -> None:
    for item in groupped_imports:
        if item.stdlib:
            item.stdlib = substitute_aliases_of_imports(
                item.stdlib,
                references_to_aliases,
            )
        if item.third_party:
            item.third_party = substitute_aliases_of_imports(
                item.third_party,
                references_to_aliases,
            )
        if item.project:
            item.project = substitute_aliases_of_imports(
                item.project,
                references_to_aliases,
            )
