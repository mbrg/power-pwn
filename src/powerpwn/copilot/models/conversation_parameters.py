from typing import NamedTuple


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
