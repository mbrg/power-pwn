from abc import ABC, abstractmethod

from powerpwn.copilot.websocket_message.websocket_parsed_message import (
    WebsocketParsedMessage,
)


class IWebsocketMessageFormatter(ABC):
    @abstractmethod
    def format(cls, message: WebsocketParsedMessage) -> str:
        """
        returns the formatted string message
        """
