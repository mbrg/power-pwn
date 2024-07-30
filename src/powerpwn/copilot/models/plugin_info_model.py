from typing import NamedTuple


class PluginInfo(NamedTuple):
    """
    Plugin info model

    """

    index: int
    id: str
    source: str
    displayName: str
