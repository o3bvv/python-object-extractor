from typing import Any, Optional, TypeVar


ObjectReference = TypeVar(
    name='ObjectReference',
    bound='ObjectReference',
)


class ObjectReference:
    __slots__ = ['module_name', 'object_name', ]

    def __init__(
        self,
        module_name: str,
        object_name: Optional[str] = None,
    ):
        self.module_name = module_name
        self.object_name = object_name

    def __repr__(self) -> str:
        object_name_repr = (
            f"'{self.object_name}'"
            if self.object_name
            else None
        )
        return (
            f"<ObjectReference("
            f"module_name='{self.module_name}', "
            f"object_name={object_name_repr})>"
        )

    def __str__(self) -> str:
        object_name = (
            self.object_name
            if self.object_name
            else "*"
        )
        return f"{self.module_name}:{object_name}"

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: Any) -> bool:
        return (
                isinstance(other, ObjectReference)
            and self.module_name == other.module_name
            and self.object_name == other.object_name
        )

    def __lt__(self, other: ObjectReference) -> bool:
        if not isinstance(other, ObjectReference):
            return NotImplemented

        return str(self) < str(other)


def make_name_from_object_reference(object_reference: ObjectReference) -> str:
    if object_reference.module_name == object_reference.object_name:
        return f"_{object_reference.module_name}"

    return (
        f"_{object_reference.module_name}_{object_reference.object_name}"
        .replace(".", "_")
    )
