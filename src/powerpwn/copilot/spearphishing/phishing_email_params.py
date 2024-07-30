from typing import NamedTuple, Optional


class PhishingEmailParameters(NamedTuple):
    """
    A model for phishing email parameters

    """

    to: str
    cc: list
    subject: Optional[str]
    body: Optional[str]
