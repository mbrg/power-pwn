import asyncio

from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum

args = ChatArguments(
        user="User",
        password="Password",
        verbose=VerboseEnum.full,
        scenario=CopilotScenarioEnum.teamshub,
        use_cached_access_token=False
    )
copilot_connector = CopilotConnector(args)

# init connection
copilot_connector.init_connection()

# send a prompt and receive an answer from Copilot
result = asyncio.get_event_loop().run_until_complete(asyncio.gather(copilot_connector.connect("Hello World")))
if result[0]:
    print(result[0].parsed_message)