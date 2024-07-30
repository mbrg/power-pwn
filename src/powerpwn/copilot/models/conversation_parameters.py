from typing import NamedTuple

from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.loggers.file_logger import FileLogger


class ConversationParameters(NamedTuple):
    """
    Chat parameters model

    """

    conversation_id: str
    session_id: str
    scenario: CopilotScenarioEnum
    url: str
    available_plugins: list
    used_plugins: list
    logger: FileLogger
