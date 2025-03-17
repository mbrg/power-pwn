import asyncio

from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.chat_automator.chat_automator import ChatAutomator
from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum

args = ChatArguments(
        user="kris@zenitystage.onmicrosoft.com",
        password="U*S+#XL)cw?d,7AQ",
        verbose=VerboseEnum.full,
        scenario=CopilotScenarioEnum.officeweb,
        use_cached_access_token=False
    )

chat_automator = ChatAutomator(args)

# init connector
chat_automator.init_connector()

# send prompt and get the answer as WebSocket message
result = chat_automator.send_prompt("Hello World")