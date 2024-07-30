from __future__ import annotations

from enum import Enum


class MessageTypeEnum(Enum):
    """
    Enum for websocket message type

    """

    user = 4
    ping = 6
    copilot = 1
    copilot_final = 2
    unknown = (
        3  # need to figure out {"type":3,"invocationId":"0"}    none = -1  # for now we are aware of {"protocol":"json","version":1} or {} messages
    )
    none = -1

    def from_int(value: int) -> MessageTypeEnum:
        if value == 4:
            return MessageTypeEnum.user
        elif value == 6:
            return MessageTypeEnum.ping
        elif value == 1:
            return MessageTypeEnum.copilot
        elif value == 2:
            return MessageTypeEnum.copilot_final
        elif value == 3:
            return MessageTypeEnum.unknown
        elif value == -1:
            return MessageTypeEnum.none
        else:
            raise ValueError(f"Invalid message type: {value}")
