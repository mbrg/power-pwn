import asyncio
from typing import Optional

from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage


class ChatAutomator:
    """
    Class that is responsible for automating the chat with Copilot (non interactive mode)
    """

    def __init__(self, arguments: ChatArguments) -> None:
        self.__copilot_connector = CopilotConnector(arguments)
        self.__is_initialized = False

    def init_connector(self) -> None:
        """
        Initializes a connection to the Copilot
        """
        if not self.__is_initialized:
            self.__copilot_connector.init_connection()
        self.__is_initialized = True

    def refresh_connector(self) -> None:
        """
        Refreshes the connection to the Copilot
        """
        self.__copilot_connector.refresh_connection()
        self.__is_initialized = True

    def send_prompt(self, prompt: str) -> Optional[WebsocketMessage]:
        """
        Sends a user prompt to the copilot and gets the response as a websocket message
        """
        self.init_connector()

        result = asyncio.get_event_loop().run_until_complete(asyncio.gather(self.__copilot_connector.connect(prompt)))

        if result[0]:
            return result[0]
        return None

    def enable_bing_web_search(self) -> None:
        """
        Enables Bing Web Search plugin
        """
        self.__copilot_connector.enable_bing_web_search()

    def disable_bing_web_search(self) -> None:
        """
        Disables Bing Web Search plugin
        """
        self.__copilot_connector.disable_bing_web_search()
