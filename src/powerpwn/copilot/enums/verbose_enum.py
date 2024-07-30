from __future__ import annotations
from enum import Enum


class VerboseEnum(Enum):
    """
    Enum for logging verbosity

    """

    off = "off"
    mid = "mid"
    full = "full"
