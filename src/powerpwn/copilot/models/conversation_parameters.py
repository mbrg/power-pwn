from typing import NamedTuple


class ConversationParameters(NamedTuple):
    """
    Chat parameters model

    """

    conversation_id: str
    session_id: str
    url: str
    available_plugins: list
    used_plugins: list
