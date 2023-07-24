from enum import Enum
from types import DynamicClassAttribute
from typing import Any, List, Optional, Type, TypeVar, cast

_TEnum = TypeVar("_TEnum", bound="StrEnum")


class StrEnum(str, Enum):
    """
    Base class for string valued enums, required for them to support JSON serialization.
    Subclasses that set values using `auto()` will have values equal to their names.
    """

    @classmethod
    def try_parse(cls: Type[_TEnum], string: str) -> Optional[_TEnum]:
        try:
            return cls(string)
        except ValueError:
            return None

    # So type checkers will recognize the return type is str
    @DynamicClassAttribute
    def value(self) -> str:
        return cast(str, super().value)

    # Type hints inspired by https://stackoverflow.com/questions/69318005/mypy-gives-an-incompatible-type-auto-expected-str-error-when-using-auto
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: List[Any]) -> str:
        """
        Uses the name as the automatic value, rather than an integer
        See https://docs.python.org/3/library/enum.html#using-automatic-values for reference
        """
        return name

    def __str__(self) -> str:
        return self.value


def strenum_to_str(enum: Optional[StrEnum]) -> str:
    return enum.value if enum is not None else "None"
