from abc import ABC, abstractmethod

from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage


class ILogger(ABC):
    @abstractmethod
    def log(self, message: WebsocketMessage) -> None:
        """
        logs a message

        :param message: message to log
        """
