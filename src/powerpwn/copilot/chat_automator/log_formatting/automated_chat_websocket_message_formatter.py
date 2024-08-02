from typing import Optional

from powerpwn.copilot.enums.message_type_enum import MessageTypeEnum
from powerpwn.copilot.websocket_message.iwebsocket_message_formatter import IWebsocketMessageFormatter
from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage
from powerpwn.copilot.websocket_message.websocket_parsed_message import WebsocketParsedMessage


class AutomatedChatWebsocketMessageFormatter(IWebsocketMessageFormatter):
    def format(self, message: Optional[WebsocketMessage]) -> Optional[str]:
        if not message:
            return None
        if message.parsed_message.type == MessageTypeEnum.copilot_final:
            if message.is_success:
                return self.__format_message_for_copilot_final(message.parsed_message)
        return message.parsed_message.copilot_message

    def __format_message_for_copilot_final(self, message: WebsocketParsedMessage) -> str:
        formatted_message = ""
        if message.copilot_message:
            formatted_message = f"{message.copilot_message}"

        return formatted_message
