from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.chat_automator.chat_automator import ChatAutomator
import os

user = os.getenv('m365user')
user_password = os.getenv('m365pass')

if user is None or user_password is None:
    raise ValueError("Environment variables for email or password are not set.")

print("User being looked at is: ", user)

args = ChatArguments(
        user=os.getenv('m365user'),
        password=os.getenv('m365pass'),
        verbose=VerboseEnum.full,
        scenario=CopilotScenarioEnum.teamshub,
        use_cached_access_token=False
    )

chat_automator = ChatAutomator(args)
chat_automator.init_connector()
result = chat_automator.send_prompt("Hello World")
