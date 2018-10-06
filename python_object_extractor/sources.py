import ast
import inspect
import itertools
import re

from types import ModuleType
from typing import Dict, Set, Iterator, Iterable, Optional

import astor

from python_object_extractor.descriptors import ObjectDescriptor
from python_object_extractor.references import ObjectReference


def get_object_source(module: ModuleType, target: object, symbol: str) -> str:
    if (
           inspect.ismodule(target)
        or inspect.isclass(target)
        or inspect.isroutine(target)
    ):
        return inspect.getsource(target)

    source = inspect.getsource(module)
    return get_assignment_source(source, symbol)


def get_assignment_source(source: str, symbol: str) -> str:
    root = ast.parse(source)

    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.AugAssign) and node.target.id == symbol:
            return astor.to_source(node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol:
                    value = astor.to_source(node.value)
                    return f"{symbol} = {value}"
                elif hasattr(target, 'elts'):
                    for i, name in enumerate(target.elts):
                        if name.id == symbol:
                            value = astor.to_source(node.value.elts[i])
                            return f"{symbol} = {value}"


def format_object_source(
    descriptor: ObjectDescriptor,
    references_to_names: Dict[ObjectReference, str],
) -> str:
    source = descriptor.source
    source = replace_access_chain_with_value(
        source=source,
        chain=[descriptor.object_reference.object_name, ],
        value=references_to_names[descriptor.object_reference],
    )

    if (
            descriptor.global_imports
        and descriptor.global_imports.project
    ):
        module_names = set()
        for item in descriptor.global_imports.project:
            while item.substituted is not None:
                item = item.substituted

            module_names.add(item.object_reference.module_name)

        if module_names:
            source = strip_imports(source, module_names)

    for object_import in descriptor.gather_imports():
        if not object_import.substituted:
            continue

        substituted_import = object_import
        while substituted_import.substituted is not None:
            substituted_import = substituted_import.substituted

        substituted_literal = (
               substituted_import.alias
            or substituted_import.object_reference.object_name
        )

        substituted_access_chain = [substituted_literal, ]
        if substituted_import.access_chain:
            substituted_access_chain.extend(substituted_import.access_chain)

        new_literal = (
               object_import.alias
            or object_import.object_reference.object_name
        )
        new_literal = references_to_names.get(
            object_import.object_reference,
            new_literal,
        )

        source = replace_access_chain_with_value(
            source=source,
            chain=substituted_access_chain,
            value=new_literal,
        )

    return source


def replace_access_chain_with_value(
    source: str,
    chain: Iterable[str],
    value: str,
) -> str:
    identifier = r"\b\s*\.\s*\b".join(chain)
    pattern = r"(([^\s\._]|^)\s*){}\b".format(identifier)
    substituted = r"\1{}".format(value)
    return re.sub(pattern, substituted, source)


def strip_imports(source: str, module_names: Set[str]) -> str:
    offsets = [0]
    offsets.extend(list(itertools.accumulate([
        len(line)
        for line in source.splitlines(keepends=True)
    ])))

    root = ast.parse(source)
    generator = _traverse_containers(root)
    previous = next(generator)
    current = None
    replacements = list()

    for current in generator:
        replacement = _maybe_get_import_replacement(previous, module_names)
        if replacement is not None:
            start = offsets[previous.lineno - 1] + previous.col_offset
            if (current.lineno - previous.lineno) < 2:
                end = offsets[current.lineno - 1] + current.col_offset
            else:
                end = offsets[current.lineno - 2] - 1
            replacements.append((start, end, replacement))
        previous = current

    if current:
        replacement = _maybe_get_import_replacement(current, module_names)
        if replacement is not None:
            replacements.append((
                offsets[previous.lineno - 1] + previous.col_offset,
                None,
                replacement,
            ))

    delta = 0
    for start, end, replacement in replacements:
        if end is None:
            end = len(source) - 1

        start -= delta
        end -= delta
        delta = (end - start) - len(replacement)
        source = source[:start] + replacement + source[end:]

    return source


def _traverse_containers(node: ast.AST) -> Iterator[ast.AST]:
    if hasattr(node, 'body'):
        for child in node.body:
            yield from _traverse_containers(child)
    else:
        yield node


def _maybe_get_import_replacement(
    node: ast.AST,
    module_names: Set[str],
) -> Optional[str]:
    if isinstance(node, ast.ImportFrom) and node.module in module_names:
        return ""

    if not isinstance(node, ast.Import):
        return

    has_import_to_replace = False
    remainders = []

    for alias in node.names:
        if alias.name in module_names:
            has_import_to_replace = True
        else:
            remainder = (
                alias.name
                if alias.asname is None
                else f"{alias.name} as {alias.asname}"
            )
            remainders.append(remainder)

    if has_import_to_replace:
        return "import " + ", ".join(remainders)
