from enum import auto

from powerpwn.enums.str_enum import StrEnum


class ResourceType(StrEnum):
    connection = auto()
    connector = auto()
    canvas_app = auto()
    principal = auto()
