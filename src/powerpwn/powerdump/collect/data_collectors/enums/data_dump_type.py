from enum import auto

from powerpwn.enums.str_enum import StrEnum


class DataDumpType(StrEnum):
    table = auto()
    collection = auto()
    attachment = auto()
    email = auto()
    secret = auto()
    key = auto()
    file = auto()
    queue_message = auto()
