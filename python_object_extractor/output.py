from typing import Dict, Iterable

from python_object_extractor.descriptors import ObjectDescriptor
from python_object_extractor.imports import ObjectImport
from python_object_extractor.imports import ObjectImportsGroupped
from python_object_extractor.modules import get_module_by_name
from python_object_extractor.modules import get_module_requirement
from python_object_extractor.references import ObjectReference
from python_object_extractor.sources import format_object_source


def output(
    module_path: str,
    requirements_path: str,
    descriptors: Iterable[ObjectDescriptor],
    imports: ObjectImportsGroupped,
    references_to_aliases: Dict[ObjectReference, str],
) -> None:
    with open(module_path, 'wt') as f:
        if imports.stdlib:
            f.write(format_imports(imports.stdlib))
            f.write("\n")

        if imports.third_party:
            f.write(format_imports(imports.third_party))
            f.write("\n")

        if imports.stdlib or imports.third_party:
            f.write("\n")

        for descriptor in descriptors:
            f.write(format_object_source(descriptor, references_to_aliases))
            f.write("\n\n")

    with open(requirements_path, 'wt') as f:
        requirements = {
            get_module_requirement(get_module_by_name(
                module_name=object_import.object_reference.module_name,
            ))
            for object_import in imports.third_party
        }
        requirements = sorted(["{}\n".format(x) for x in requirements])
        f.writelines(requirements)
        f.write("\n")


def format_imports(imports: Iterable[ObjectImport]) -> str:
    lines = []

    imports_of_modules = sorted([
        str(x) for x in imports if x.is_import_of_module()
    ])
    lines.extend(imports_of_modules)
    if imports_of_modules:
        lines.append("")

    imports_from_modules = sorted([
        str(x) for x in imports if x.is_import_from_module()
    ])
    lines.extend(imports_from_modules)
    if imports_from_modules:
        lines.append("")

    return "\n".join(lines)
