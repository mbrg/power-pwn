from typing import NamedTuple, Optional

from powerpwn.copilot.models.agent_info_model import AgentInfoModel


class ConversationParameters(NamedTuple):
    """
    Chat parameters model

    """

    conversation_id: str
    session_id: str
    url: str
    used_plugins: list
    available_gpts: list
    used_agent: list
