from typing import NamedTuple


class AgentInfoModel(NamedTuple):
    """
    Agent info model

    """

    index: int
    id: str
    displayName: str
    description: str
    source: str
    version: str
    type: str
