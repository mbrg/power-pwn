import pathlib
import subprocess  # nosec
import uuid
from typing import Optional

import jwt
import requests
import websockets

from powerpwn.common.cache.cached_entity import CachedEntity
from powerpwn.common.cache.token_cache import TokenCache
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.message_type_enum import MessageTypeEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.exceptions.copilot_connected_user_mismatch import CopilotConnectedUserMismatchException
from powerpwn.copilot.exceptions.copilot_connection_failed_exception import CopilotConnectionFailedException
from powerpwn.copilot.exceptions.copilot_connection_not_initialized_exception import CopilotConnectionNotInitializedException
from powerpwn.copilot.loggers.file_logger import FileLogger
from powerpwn.copilot.models.agent_info_model import AgentInfoModel
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.models.conversation_parameters import ConversationParameters
from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage

TOOL_PROMPT = "[Tool]: "


class CopilotConnector:
    """
    A class that is responsible for connecting and interacting with the Copilot
    """

    _SUBSTRATE_TOKEN_CACHE_KEY = "substrate_access_token"  # nosec

    def __init__(self, arguments: ChatArguments) -> None:
        self.__is_initialized = False
        self.__arguments = arguments
        self.__conversation_params: Optional[ConversationParameters] = None
        self.__index = 0
        self.__token_cache = TokenCache()
        self.__file_logger: Optional[FileLogger] = None

    def init_connection(self) -> None:
        """
        Initializes the connection with the Copilot
        """
        if self.__is_initialized:
            return

        self.__conversation_params = self.__get_conversation_parameters()
        self.__file_logger = FileLogger(f"session_{self.__conversation_params.session_id}.log")

        self.__is_initialized = True

    def refresh_connection(self) -> None:
        """
        Refresh the connection with the Copilot
        """
        self.__conversation_params = self.__get_conversation_parameters(True)
        self.__file_logger = FileLogger(f"session_{self.__conversation_params.session_id}.log")

        self.__is_initialized = True

    @property
    def conversation_parameters(self) -> ConversationParameters:
        # if connection was not initialized correctly, an exception will be raised
        self.init_connection()
        return self.__conversation_params

    async def connect(self, prompt: str) -> Optional[WebsocketMessage]:
        """
        Connects to the Copilot via a websocket and sends a prompt

        :param prompt: prompt to send

        raises CopilotConnectionNotInitializedException: when sending a prompt without initializing the connection

        returns: the response from the Copilot as a WebsocketMessage
        """
        if not self.__is_initialized:
            raise CopilotConnectionNotInitializedException("Copilot connection not initialized.")

        url = self.__conversation_params.url

        protocol_message = {"protocol": "json", "version": 1}
        ping_message = {"type": 6}

        inputs = [protocol_message, ping_message, self.__get_prompt(prompt)]

        async with websockets.connect(url) as websocket:
            for input in inputs:
                payload = WebsocketMessage.to_websocket_message(input)
                websocket_payload = WebsocketMessage(payload)
                self.__log(websocket_payload)
                is_user_input = websocket_payload.type() == MessageTypeEnum.user
                await websocket.send(payload)
                stop_polling = False
                while not stop_polling:
                    response = await websocket.recv()
                    websocket_message = WebsocketMessage(response)
                    self.__log(websocket_message)
                    parsed_message = websocket_message.parsed_message
                    interaction_type = parsed_message.type

                    if (
                        interaction_type in (MessageTypeEnum.none, MessageTypeEnum.copilot_final, MessageTypeEnum.unknown)
                        or interaction_type == MessageTypeEnum.ping
                        and not is_user_input
                    ):
                        stop_polling = True
                        if interaction_type == MessageTypeEnum.copilot_final:
                            return websocket_message
                        elif interaction_type == MessageTypeEnum.unknown:
                            print(f"{TOOL_PROMPT} Got unknown message type : {websocket_message.message}")

    def enable_bing_web_search(self) -> None:
        if not self.__is_initialized:
            raise CopilotConnectionNotInitializedException("Copilot connection not initialized.")
        self.__conversation_params.used_plugins.append({"Id": "BingWebSearch", "Source": "BuiltIn"})

    def disable_bing_web_search(self) -> None:
        if not self.__is_initialized:
            raise CopilotConnectionNotInitializedException("Copilot connection not initialized.")
        self.__conversation_params.used_plugins = []

    def use_agent(self, agent_index: int) -> str:
        if not self.__is_initialized:
            raise CopilotConnectionNotInitializedException("Copilot connection not initialized.")
        if agent_index >= len(self.__conversation_params.available_gpts):
            print(f"Invalid agent index: {agent_index}")
            return
        agent = self.__conversation_params.available_gpts[agent_index]
        self.__conversation_params.used_agent.append(agent)
        return agent.displayName

    def use_copilot365(self) -> None:
        if not self.__is_initialized:
            raise CopilotConnectionNotInitializedException("Copilot connection not initialized.")
        self.__conversation_params.used_agent.pop()

    def __get_session_from_url(self, url: str) -> str:
        if "X-SessionId=" not in url:
            raise ValueError("Session ID not found in URL.")
        return url.split("X-SessionId=")[1].split("&")[0]

    def __get_prompt(self, prompt: str) -> dict:
        is_start_of_session = self.__index == 0
        used_agent_params = {}
        if len(self.__conversation_params.used_agent) > 0:
            used_agent = self.__conversation_params.used_agent[0]
            used_agent_params = {"id": used_agent.id, "source": used_agent.source}

        prompt_message_dict = {
            "arguments": [
                {
                    "source": self.__arguments.scenario.value,
                    "clientCorrelationId": "60c2ee92-64f1-cef5-555a-b7ad5ad2c21c",
                    "sessionId": self.__conversation_params.session_id,
                    "optionsSets": [
                        "enterprise_flux_web",
                        "enterprise_flux_work",
                        "enable_request_response_interstitials",
                        "enterprise_flux_image_v1",
                        "enterprise_toolbox_with_skdsstore",
                        "enterprise_toolbox_with_skdsstore_search_message_extensions",
                        "enable_ME_auth_interstitial",
                        "skdsstorethirdparty",
                        "enable_confirmation_interstitial",
                        "enable_plugin_auth_interstitial",
                        "enable_response_action_processing",
                        "enterprise_flux_work_gptv",
                        "enterprise_flux_work_code_interpreter",
                        "enable_batch_token_processing",
                    ],
                    "options": {},
                    "allowedMessageTypes": [
                        "Chat",
                        "Suggestion",
                        "InternalSearchQuery",
                        "InternalSearchResult",
                        "Disengaged",
                        "InternalLoaderMessage",
                        "RenderCardRequest",
                        "AdsQuery",
                        "SemanticSerp",
                        "GenerateContentQuery",
                        "SearchQuery",
                        "ConfirmationCard",
                        "AuthError",
                        "DeveloperLogs",
                    ],
                    "sliceIds": [],
                    "threadLevelGptId": used_agent_params,
                    "conversationId": self.__conversation_params.conversation_id,
                    "traceId": "6eaf112117f7ecbfa4cef5495f098e59",
                    "isStartOfSession": is_start_of_session,
                    "productThreadType": "Office",
                    "clientInfo": {"clientPlatform": "web"},
                    "message": {
                        "author": "user",
                        "inputMethod": "Keyboard",
                        "text": prompt,
                        "entityAnnotationTypes": ["People", "File", "Event", "Email", "TeamsMessage"],
                        "requestId": "6eaf112117f7ecbfa4cef5495f098e59",
                        "locationInfo": {"timeZoneOffset": 3, "timeZone": "Asia/Jerusalem"},
                        "locale": "en-US",
                        "messageType": "Chat",
                        "experienceType": "Default",
                    },
                    "plugins": self.__conversation_params.used_plugins,
                }
            ],
            "invocationId": str(self.__index),
            "target": "chat",
            "type": 4,
        }

        if used_agent_params:
            prompt_message_dict["arguments"][0]["gpts"] = [used_agent_params]

        return prompt_message_dict

    def __get_access_token(self, refresh: bool = False) -> Optional[str]:
        scenario = self.__arguments.scenario
        user = self.__arguments.user
        password = self.__arguments.password

        access_token: Optional[str] = None
        if self.__arguments.use_cached_access_token or refresh:
            if access_token := self.__get_access_token_from_cache():
                print("Access token retrieved from cache.")
                return access_token
            else:
                if not self.__arguments.password:
                    raise CopilotConnectionFailedException(
                        "Could not get access token to connect to copilot from cache, and no password is provided."
                    )

        print("Falling back to getting access token with user password sign in..")

        module = "get_substrate_bearer_office" if scenario == CopilotScenarioEnum.officeweb else "get_substrate_bearer_teams"
        try:
            # Run the Node.js script using subprocess
            result = subprocess.run(  # nosec
                [
                    "node",
                    pathlib.Path("puppeteer_get_substrate_bearer") / f"{module}.js",  # nosec
                    f"user={user}",  # nosec
                    f"password={password}",  # nosec
                ],
                capture_output=True,
                text=True,
            )

            # Print any error messages
            if result.stderr:
                print("Node.js Errors:")
                print(result.stderr)

            access_token_array = result.stdout.split("access_token:")
            if len(access_token_array) < 2 or access_token_array[1] == "null":
                print("Failed to get access token. Exiting...")
                return None
            access_token = access_token_array[1].strip()
            self.__token_cache.put_token(CachedEntity(key=self._SUBSTRATE_TOKEN_CACHE_KEY, val=access_token))
            print(f"Access token cached successfully in {self.__token_cache.cache_path}.")
            return access_token

        except FileNotFoundError:
            print("Node.js executable not found. Please make sure Node.js is installed and in your PATH.")
            return None

    def __get_access_token_from_cache(self) -> Optional[str]:
        token = self.__token_cache.try_fetch_token(self._SUBSTRATE_TOKEN_CACHE_KEY)
        if not token:
            print("Access token does not exist in cache.")
            return None
        return token

    def __get_websocket_url(self, bearer_token: str, scenario: CopilotScenarioEnum, parsed_token: dict) -> str:
        session_id = uuid.uuid4()
        client_request_id = uuid.uuid4()

        tenant_id = parsed_token.get("tid")
        object_id = parsed_token.get("oid")

        if not tenant_id or not object_id:
            raise ValueError("Failed to parse tenant_id or object_id from bearer token.")

        prefix = f"wss://substrate.office.com/m365Copilot/Chathub/{object_id}@{tenant_id}?X-ClientRequestId={client_request_id}&X-SessionId={session_id}&access_token={bearer_token}"

        return (
            f"{prefix}&X-variants=feature.includeExternal,feature.AssistantConnectorsContentSources,3S.BizChatWprBoostAssistant,3S.EnableMEFromSkillDiscovery,feature.EnableAuthErrorMessage,EnableRequestPlugins,feature.EnableSensitivityLabels,feature.IsEntityAnnotationsEnabled,EnableUnsupportedUrlDetector&source=%22officeweb%22&scenario=officeweb"
            if scenario == CopilotScenarioEnum.officeweb
            else f"{prefix}&X-variants=feature.includeExternal,feature.AssistantConnectorsContentSources,3S.BizChatWprBoostAssistant,3S.EnableMEFromSkillDiscovery,feature.EnableAuthErrorMessage,feature.EnableRequestPlugins,3S.SKDS_EnablePluginManagement,EnableRequestPlugins,feature.EnableSensitivityLabels,feature.IsEntityAnnotationsEnabled,EnableUnsupportedUrlDetector&source=%22teamshub%22&scenario=teamshub"
        )

    def __get_available_agents(self, access_token: str) -> list:
        if self.__arguments.scenario == CopilotScenarioEnum.teamshub:
            return []

        agents: list[AgentInfoModel] = []
        url = "https://substrate.office.com/m365Copilot/GetGptList"

        url = "https://substrate.office.com/m365Copilot//GetGptList?request=%7B%22optionsSets%22%3A%5B%22flux_gpt_data_retriever_enterprise%22%2C%22plugins_as_declarative_agents%22%5D%2C%22traceId%22%3A%228883a40d990df8b1fb0c9b3166a9b78e%22%7D&variants=feature.disabledisallowedmsgs"

        headers = {"Authorization": f"Bearer {access_token}", "X-Scenario": "officeweb"}

        agents_response = requests.get(url, headers=headers)  # nosec
        if agents_response.status_code != 200:
            if agents_response.status_code == 401:
                raise CopilotConnectionFailedException("Unauthorized. Try to delete cached token and retry")
            print(f"Failed to get agents. Error: {agents_response.text}. status_code: {agents_response.status_code}")
            return []
        for index, agent in enumerate(agents_response.json().get("gptList", [])):
            gpt_identifier = agent.get("gptIdentifier")
            agents.append(
                AgentInfoModel(
                    index=index,
                    id=gpt_identifier["id"],
                    displayName=agent["name"],
                    version=gpt_identifier.get("version", "N/A"),
                    description=agent.get("description", "N/A"),
                    source=gpt_identifier["source"],
                    type=agent.get("type"),
                )
            )
        return agents

    def __get_conversation_parameters(self, refresh: bool = False) -> ConversationParameters:
        print("Getting bearer token...")
        access_token = self.__get_access_token(refresh)
        if not access_token:
            print("Failed to get bearer token. Exiting...")
            raise CopilotConnectionFailedException("Could not get access token to connect to copilot.")

        parsed_jwt = jwt.decode(access_token, algorithms=["RS256"], options={"verify_signature": False})
        upn = parsed_jwt.get("upn")
        unique_name = parsed_jwt.get("unique_name")

        if self.__arguments.user not in (upn, unique_name):
            raise CopilotConnectedUserMismatchException("Cached token is not for the user provided in the arguments.")

        print("Acquired bearer token successfully.")
        url = self.__get_websocket_url(access_token, self.__arguments.scenario, parsed_jwt)
        session_id = self.__get_session_from_url(url)

        available_agents: list[AgentInfoModel] = self.__get_available_agents(access_token)

        return ConversationParameters(
            conversation_id=str(uuid.uuid4()), url=url, session_id=session_id, used_plugins=[], available_gpts=available_agents, used_agent=[]
        )

    def __log(self, message: WebsocketMessage) -> None:
        if self.__arguments.verbose == VerboseEnum.off or not self.__file_logger:
            return None
        elif (
            self.__arguments.verbose == VerboseEnum.mid and message.type() != MessageTypeEnum.copilot
        ) or self.__arguments.verbose == VerboseEnum.full:
            self.__file_logger.log(message.message)
