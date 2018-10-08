import io
import sys

from pathlib import Path
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
    if module_path == '-':
        output_module(sys.stdout, descriptors, imports, references_to_aliases)
    else:
        module_path = Path(module_path)
        module_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        with module_path.open('wt') as f:
            output_module(f, descriptors, imports, references_to_aliases)

    if requirements_path == '-':
        output_requirements(sys.stdout, imports)
    else:
        requirements_path = Path(requirements_path)
        requirements_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        with requirements_path.open('wt') as f:
            output_requirements(f, imports)


def output_module(
    output_stream: io.TextIOBase,
    descriptors: Iterable[ObjectDescriptor],
    imports: ObjectImportsGroupped,
    references_to_aliases: Dict[ObjectReference, str],
) -> None:
    if imports.stdlib:
        output_stream.write(format_imports(imports.stdlib))
        output_stream.write("\n")

    if imports.third_party:
        output_stream.write(format_imports(imports.third_party))
        output_stream.write("\n")

    if imports.stdlib or imports.third_party:
        output_stream.write("\n")

    for descriptor in descriptors:
        source = format_object_source(descriptor, references_to_aliases)
        output_stream.write(source)
        output_stream.write("\n\n")

    output_stream.flush()


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


def output_requirements(
    output_stream: io.TextIOBase,
    imports: ObjectImportsGroupped,
) -> None:
    requirements = {
        get_module_requirement(get_module_by_name(
            module_name=object_import.object_reference.module_name,
        ))
        for object_import in imports.third_party
    }
    requirements = sorted(["{}\n".format(x) for x in requirements])
    output_stream.writelines(requirements)
    output_stream.write("\n")
    output_stream.flush()
