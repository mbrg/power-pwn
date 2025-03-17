import asyncio

from powerpwn.copilot.copilot_connector.copilot_connector import TOOL_PROMPT, CopilotConnector
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
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
    _ENABLE_BING_WEB_SEARCH_PROMPT = "enable BingWebSearch"
    _DISABLE_BING_WEB_SEARCH_PROMPT = "disable BingWebSearch"
    _LIST_AVAILABLE_AGENTS_PROMPT = "list available agents"
    _USE_AGENT_PROMPT = "use agent"
    _USE_COPILOT365_PROMPT = "use copilot365"

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

                if prompt == self._LIST_AVAILABLE_AGENTS_PROMPT:
                    print(f"{TOOL_PROMPT}Available agents:")
                    for agent in conversation_parameters.available_gpts:
                        print(f"[{agent.index}] - {agent.displayName}({agent.version})")
                        print(f"\t{agent.description}")
                    print(f"{TOOL_PROMPT}To switch to agent, type '{self._USE_AGENT_PROMPT} <agent_index>'")
                    print(f"{TOOL_PROMPT}To switch to copilot365, type '{self._USE_COPILOT365_PROMPT}'")
                    continue

                if prompt.startswith(self._USE_AGENT_PROMPT):
                    self.__use_agent(prompt)
                    continue
                if prompt == self._USE_COPILOT365_PROMPT:
                    self.__copilot_connector.use_copilot365()
                    continue
                if prompt == self._ENABLE_BING_WEB_SEARCH_PROMPT:
                    self.__copilot_connector.enable_bing_web_search()
                    print(f"{TOOL_PROMPT}Bing Web Search enabled.")
                    continue
                if prompt == self._DISABLE_BING_WEB_SEARCH_PROMPT:
                    self.__copilot_connector.disable_bing_web_search()
                    print(f"{TOOL_PROMPT}Bing Web Search disabled.")
                    continue
                result = asyncio.get_event_loop().run_until_complete(asyncio.gather(self.__copilot_connector.connect(prompt)))
                if result[0]:
                    print(self.__websocket_formatter.format(result[0].parsed_message))
                    if result[0].parsed_message.is_disengaged:
                        print(f"{TOOL_PROMPT}Conversation is disengaged, re-initiating connection.")
                        self.__copilot_connector.refresh_connection()
                        print(f"{TOOL_PROMPT}Connection refreshed.")

        except CopilotConnectionNotInitializedException as e:
            print(f"{TOOL_PROMPT}{e.message}")
        except CopilotConnectionFailedException as e:
            print(f"{TOOL_PROMPT}{e.message}")
        except CopilotConnectedUserMismatchException as e:
            print(f"{TOOL_PROMPT}{e.message}")
        except Exception as e:
            print(f"{TOOL_PROMPT}An error occurred: {e}")

    def __use_agent(self, prompt: str) -> None:
        agent_index = int(prompt.split(self._USE_AGENT_PROMPT)[1].strip())
        self.__copilot_connector.use_agent(agent_index)

if __name__ == "__main__":
    arguments = ChatArguments("kris@zenitystage.onmicrosoft.com", "U*S+#XL)cw?d,7AQ", True, CopilotScenarioEnum.officeweb, VerboseEnum.off)
    chat = InteractiveChat(arguments)
    chat.start_chat()