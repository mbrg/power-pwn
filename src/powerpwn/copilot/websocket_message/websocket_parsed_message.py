from typing import NamedTuple

from powerpwn.copilot.enums.message_type_enum import MessageTypeEnum


class WebsocketParsedMessage(NamedTuple):
    """
    Websocket parsed message model

    """

    copilot_message: str
    is_success: bool
    is_disengaged: bool
    suggestions: list
    type: MessageTypeEnum
