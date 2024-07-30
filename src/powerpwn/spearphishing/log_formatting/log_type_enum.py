from enum import auto, Enum


class LogType(Enum):
    """
    Enum for log type

    """

    none = auto()
    tool = auto()
    prompt = auto()
    response = auto()
