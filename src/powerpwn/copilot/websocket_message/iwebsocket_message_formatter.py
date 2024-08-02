from abc import ABC, abstractmethod
from typing import Optional

from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage


class IWebsocketMessageFormatter(ABC):
    @abstractmethod
    def format(cls, message: Optional[WebsocketMessage]) -> Optional[str]:
        """
        returns the formatted string message
        """
