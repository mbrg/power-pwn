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

    def send_prompt(self, prompt: str) -> Optional[WebsocketMessage]:
        """
        Sends a user prompt to the copilot and gets the response as a websocket message
        """
        self.init_connector()

        result = asyncio.get_event_loop().run_until_complete(
            asyncio.gather(
                self.__copilot_connector.connect(
                    prompt,
                )
            )
        )

        if result[0]:
            return result[0]
        return None

    def add_plugins(self, plugin_indices: list) -> None:
        """
        Adds plugins to the conversation

        :param plugin_ids: list of plugin indices as they appear in the available plugins list
        """
        self.__copilot_connector.add_plugins(plugin_indices)

    def get_available_plugins(self) -> list:
        """
        Returns the available plugins for the conversation
        """
        return self.__copilot_connector.conversation_parameters.available_plugins
