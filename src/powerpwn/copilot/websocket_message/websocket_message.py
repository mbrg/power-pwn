import json
from typing import Final, Optional

from typing_extensions import override

from powerpwn.copilot.enums.message_type_enum import MessageTypeEnum
from powerpwn.copilot.websocket_message.iwebsocket_message import IWebsocketMessage
from powerpwn.copilot.websocket_message.websocket_parsed_message import WebsocketParsedMessage

COPILOT_PROMPT = "[Copilot]: "
SUGGESTIONS = "Suggestions:"


class WebsocketMessage(IWebsocketMessage):
    __SPECIAL_CHAR: Final[str] = chr(30)

    def __init__(self, message: str):
        self.__message = message
        self.__json_message = json.loads(self.__message.split(self.__SPECIAL_CHAR)[0])
        self.__type = MessageTypeEnum.from_int(self.__json_message.get("type", -1))
        self.__parsed_message: Optional[WebsocketParsedMessage] = None

    @property
    @override
    def message(self) -> str:
        return self.__message

    @property
    @override
    def parsed_message(self) -> WebsocketParsedMessage:
        if not self.__parsed_message:
            self.__parsed_message = self.__parse()
        return self.__parsed_message

    @override
    def formatted_str(self) -> str:
        # TODO: handle cases where message is not found, and ping the server
        if self.type() == MessageTypeEnum.copilot_final:
            if self.is_success():
                return self.__parse_message_for_copilot_final()
            return self.__parse_message_for_copilot_final_failed()
        return self.message

    @override
    def type(self) -> MessageTypeEnum:
        return self.__type

    @override
    def is_success(self) -> bool:
        return self.__json_message["item"]["result"]["value"] in ("Success", "ApologyResponseReturned")

    @classmethod
    def to_websocket_message(cls, message: dict) -> str:
        return json.dumps(message) + cls.__SPECIAL_CHAR

    def __parse(self) -> WebsocketParsedMessage:
        copilot_message: str = ""
        suggestions: list[str] = []
        is_disengaged = False

        is_success = True

        if self.type() == MessageTypeEnum.copilot_final:
            is_success = self.__json_message["item"]["result"]["value"] in ("Success", "ApologyResponseReturned")

            if not is_success:
                copilot_message = self.__parse_message_for_copilot_final_failed()
            else:
                messages = self.__json_message["item"]["messages"]
                for message in messages:
                    message_type = message["messageType"]
                    if message["author"] == "bot":
                        if message_type == "Chat":
                            copilot_message = message["text"]
                            message_suggestions = message.get("suggestedResponses", [])
                            for suggestion in message_suggestions:
                                suggestions.append(suggestion["text"])
                        elif message_type == "Disengaged":
                            copilot_message = message["hiddenText"]
                            is_disengaged = True
                            break

        return WebsocketParsedMessage(
            copilot_message=copilot_message, is_success=is_success, is_disengaged=is_disengaged, suggestions=suggestions, type=self.type()
        )

    def __parse_message_for_copilot_final(self) -> str:
        messages = self.__json_message["item"]["messages"]
        copilot_message = ""
        suggestions: list[str] = []
        is_disengaged = False
        for message in messages:
            message_type = message["messageType"]
            if message["author"] == "bot":
                if message_type == "Chat":
                    copilot_message = message["text"]
                    message_suggestions = message.get("suggestedResponses", [])
                    for suggestion in message_suggestions:
                        suggestions.append(suggestion["text"])
                elif message_type == "Disengaged":
                    copilot_message = message["hiddenText"]
                    is_disengaged = True
                    break

        if copilot_message:
            formatted_message = f"{COPILOT_PROMPT}{copilot_message}\n"

        if not is_disengaged and len(suggestions) > 0:
            formatted_message += f"{SUGGESTIONS}\n"
            for idx, suggestion in enumerate(suggestions):
                formatted_message += f"{idx + 1}. {suggestion}\n"

        return formatted_message

    def __parse_message_for_copilot_final_failed(self) -> str:
        parsed_message = ""
        message = self.__json_message["item"]["result"]["message"]
        parsed_message = f"Error: {message}\n"
        if "exception" in self.__json_message["item"]["result"]:
            exception = self.__json_message["item"]["result"]["exception"]
            parsed_message += f"Exception: {exception}\n"
        if "value" in self.__json_message["item"]["result"]:
            value = self.__json_message["item"]["result"]["value"]
            parsed_message += f"Value: {value}"
        return parsed_message
