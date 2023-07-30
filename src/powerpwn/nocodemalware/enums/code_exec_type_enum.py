from enum import auto

from powerpwn.enums.str_enum import StrEnum


class CodeExecTypeEnum(StrEnum):
    python = auto()
    visualbasic = auto()
    javascript = auto()
    powershell = auto()
    commandline = auto()
