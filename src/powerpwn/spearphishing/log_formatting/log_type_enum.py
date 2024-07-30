from enum import Enum, auto


class LogType(Enum):
    """
    Enum for log type

    """

    none = auto()
    tool = auto()
    prompt = auto()
    response = auto()
