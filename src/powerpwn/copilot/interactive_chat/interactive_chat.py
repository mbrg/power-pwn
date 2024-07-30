import asyncio

from powerpwn.copilot.copilot_connector.copilot_connector import TOOL_PROMPT, CopilotConnector
from powerpwn.copilot.enums.plugin_action_enum import PluginActionEnum
from powerpwn.copilot.exceptions.copilot_connected_user_mismatch import CopilotConnectedUserMismatchException
from powerpwn.copilot.exceptions.copilot_connection_failed_exception import CopilotConnectionFailedException
from powerpwn.copilot.exceptions.copilot_connection_not_initialized_exception import CopilotConnectionNotInitializedException
from powerpwn.copilot.interactive_chat.interactive_chat_websocket_formatter import InterActiveChatWebsocketMessageFormatter
from powerpwn.copilot.models.chat_argument import ChatArguments


class InteractiveChat:
    """
    A class that is responsible for the interactive chat with Copilot (interactive mode)
    """

    _USER_PROMPT = "[User]: "
    _SELECT_PLUGIN_PROMPT_PREFIX = "select plugins "
    _UNSELECT_PLUGIN_PROMPT_PREFIX = "unselect plugins "
    _AVAILABLE_PLUGINS_PROMPT = "list available plugins"
    _EXIT_PROMPT = "exit"

    def __init__(self, parsed_args: ChatArguments) -> None:
        self.__copilot_connector = CopilotConnector(parsed_args)
        self.__websocket_formatter = InterActiveChatWebsocketMessageFormatter()

    def start_chat(self):
        """
        Starts the interactive chat with Copilot
        """
        try:
            conversation_parameters = self.__copilot_connector.conversation_parameters

            print(f"Connecting to websocket with session {conversation_parameters.session_id}...")

            while True:
                prompt = input(self._USER_PROMPT).strip().lower()
                if prompt == self._EXIT_PROMPT:
                    print("Exiting...")
                    break
                if prompt == self._AVAILABLE_PLUGINS_PROMPT:
                    print(f"{TOOL_PROMPT}Available plugins:")
                    for plugin in conversation_parameters.available_plugins:
                        print(f"[{plugin.index}] - {plugin.displayName} - {plugin.id}")
                    print(f"{TOOL_PROMPT}To select plugins, type '{self._SELECT_PLUGIN_PROMPT_PREFIX}<idx1>,<idx2>,...'")
                    print(f"{TOOL_PROMPT}To unselect plugins, type '{self._UNSELECT_PLUGIN_PROMPT_PREFIX}<idx1>,<idx2>,...'")
                    continue
                if prompt.startswith(self._SELECT_PLUGIN_PROMPT_PREFIX):
                    self.__add_plugins(prompt)
                    continue
                if prompt.startswith(self._UNSELECT_PLUGIN_PROMPT_PREFIX):
                    self.__remove_plugins(prompt)
                    continue
                result = asyncio.get_event_loop().run_until_complete(asyncio.gather(self.__copilot_connector.connect(prompt)))
                if result[0]:
                    print(self.__websocket_formatter.format(result[0].parsed_message))

        except CopilotConnectionNotInitializedException as e:
            print(f"{TOOL_PROMPT}{e.message}")
        except CopilotConnectionFailedException as e:
            print(f"{TOOL_PROMPT}{e.message}")
        except CopilotConnectedUserMismatchException as e:
            print(f"{TOOL_PROMPT}{e.message}")
        except Exception as e:
            print(f"{TOOL_PROMPT}An error occurred: {e}")

    def __add_plugins(self, prompt: str) -> None:
        self.__copilot_connector.add_plugins(self.__extract_plugins(prompt, PluginActionEnum.add))

    def __remove_plugins(self, prompt: str) -> None:
        self.__copilot_connector.remove_plugins(self.__extract_plugins(prompt, PluginActionEnum.remove))

    def __extract_plugins(self, prompt: str, action: PluginActionEnum) -> None:
        separator = self._SELECT_PLUGIN_PROMPT_PREFIX if action == PluginActionEnum.add else self._UNSELECT_PLUGIN_PROMPT_PREFIX
        error_message = f"{TOOL_PROMPT}No plugins selected." if action == PluginActionEnum.add else "No plugins to unselect"

        plugins_str = prompt.split(separator)
        if len(plugins_str) < 2:
            print(error_message)
            return []

        plugin_indices = plugins_str[1].split(",")
        return [int(plugin_index) for plugin_index in plugin_indices]
