from powerpwn.enums.str_enum import StrEnum


class CommandToRunEnum(StrEnum):
    EXFILTRATION = "exflirtate"
    RANSOMWARE = "ransomware"
    CODE_EXEC = "command-exec"
    CLEANUP = "cleanup"
    STEAL_POWER_AUTOMATE_TOKEN = "steal-power-automate-token"
    STEAL_COOKIE = "steal-cookie"
