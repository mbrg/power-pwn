from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.chat_automator.chat_automator import ChatAutomator
from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector
import os
import asyncio

user = os.getenv('m365user')
user_password = os.getenv('m365pass')
init_prompt = os.getenv('initprompt')

if user is None or user_password is None:
    raise ValueError("Environment variables for email or password are not set.")

print("User being looked at is: ", user)

print("Initial Prompt: ", init_prompt)

args = ChatArguments(
        user=os.getenv('m365user'),
        password=os.getenv('m365pass'),
        verbose=VerboseEnum.full,
        scenario=CopilotScenarioEnum.officeweb,
        use_cached_access_token=False
    )

copilot_connector = CopilotConnector(args)

# init connection
copilot_connector.init_connection()

# send a prompt and receive an answer from Copilot
result = asyncio.get_event_loop().run_until_complete(asyncio.gather(copilot_connector.connect(os.getenv(init_prompt))))
if result[0]:
    print(result[0].parsed_message)
