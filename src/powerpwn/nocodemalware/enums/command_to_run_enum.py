from powerpwn.enums.str_enum import StrEnum


class CommandToRunEnum(StrEnum):
    EXFILTRATION = "exfiltrate"
    RANSOMWARE = "ransomware"
    CODE_EXEC = "command-exec"
    CLEANUP = "cleanup"
    STEAL_POWER_AUTOMATE_TOKEN = "steal-power-automate-token"  # nosec
    STEAL_COOKIE = "steal-cookie"
