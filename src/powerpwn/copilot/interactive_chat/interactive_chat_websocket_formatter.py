from powerpwn.copilot.enums.message_type_enum import MessageTypeEnum
from powerpwn.copilot.websocket_message.iwebsocket_message_formatter import IWebsocketMessageFormatter
from powerpwn.copilot.websocket_message.websocket_parsed_message import WebsocketParsedMessage


class InterActiveChatWebsocketMessageFormatter(IWebsocketMessageFormatter):
    __SUGGESTIONS_PREFIX = "Suggestions:"
    _COPILOT_PROMPT = "[Copilot]: "

    def format(self, message: WebsocketParsedMessage) -> str:
        if message.type == MessageTypeEnum.copilot_final:
            if message.is_success:
                return self.__format_message_for_copilot_final(message)
        return message.copilot_message

    def __format_message_for_copilot_final(self, message: WebsocketParsedMessage) -> str:
        formatted_message = ""
        if message.copilot_message:
            formatted_message = f"{self._COPILOT_PROMPT}{message.copilot_message}\n"

        if not message.is_disengaged and len(message.suggestions) > 0:
            formatted_message += f"{self.__SUGGESTIONS_PREFIX}\n"
            for idx, suggestion in enumerate(message.suggestions):
                formatted_message += f"{idx + 1}. {suggestion}\n"

        return formatted_message
