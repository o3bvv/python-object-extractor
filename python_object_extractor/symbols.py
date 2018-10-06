import builtins
import symtable

from typing import List, Set


BUILTINS = set(dir(builtins) + ['__class__', ])


def extract_symbols_from_source(
    source: str,
) -> List[symtable.Symbol]:
    table = symtable.symtable(source, "<unknown>", "exec")
    return extract_symbols_from_table(table)


def extract_symbols_from_table(
    table: symtable.SymbolTable,
    parent_symbols: Set = None,
) -> List[symtable.Symbol]:
    result = [
        x
        for x in table.get_symbols()
        if (
                not x.is_parameter()
            and not x.is_assigned()
            and not (parent_symbols and x.get_name() in parent_symbols)
            and x.is_referenced()
            and (x.get_name() not in BUILTINS)
        )
    ]

    for child in table.get_children():
        own_symbols = {
            x.get_name()
            for x in table.get_symbols()
            if x.is_parameter() or x.is_assigned()
        }
        if parent_symbols:
            own_symbols |= parent_symbols
        result.extend(extract_symbols_from_table(child, own_symbols))

    return result


def contains_import_symbols(
    symbols: List[symtable.Symbol],
) -> bool:
    return any([
        x for x in symbols
        if x.is_imported()
    ])


def exclude_import_symbols(
    symbols: List[symtable.Symbol],
) -> List[symtable.Symbol]:
    return [
        x for x in symbols
        if not x.is_imported()
    ]
