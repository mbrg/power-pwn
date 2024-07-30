from typing import NamedTuple, Optional

from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum


class ChatArguments(NamedTuple):
    """
    Chat arguments model

    """

    user: str
    password: str
    use_cached_access_token: Optional[bool]
    scenario: CopilotScenarioEnum
    verbose: VerboseEnum
