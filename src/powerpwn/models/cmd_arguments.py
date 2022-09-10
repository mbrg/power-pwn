from enum import Enum, auto

from pydantic import BaseModel, Field


class CommandToRunEnum(Enum):
    EXFILTRATION = auto()
    RANSOMWARE = auto()
    CODE_EXEC = auto()
    CLEANUP = auto()
    STEAL_POWER_AUTOMATE_TOKEN = auto()
    STEAL_COOKIE = auto()


class CodeExecTypeEnum(Enum):
    PYTHON = auto()
    VISUALBASIC = auto()
    JAVASCRIPT = auto()
    POWERSHELL = auto()
    COMMANDLINE = auto()
    EMPTY = ""


class CommandArguments(BaseModel):
    command_to_run: CommandToRunEnum
    exfiltrate_target_file: str = Field(default="", help="Absolute path to file")
    ransomware_crawl_depth: str = Field(default="", help="Recursively search into subdirectories this many times")
    ransomware_directories_to_init_crawl: str = Field(
        default="", help="A list of directories to begin crawl from separated by a command (e.g.'C:\\,D:\\')"
    )
    ransomware_encryption_key: str = Field(default="", help="an encryption key used to encrypt each file identified (AES256)")
    code_exec_command_type: CodeExecTypeEnum = Field(default="", help="Execution environment")
    code_exec_command: str = Field(default="", help="A command to execute encoded as a string")
    steal_cookie_fqdn: str = Field(default="", help="fully qualified domain name to fetch the cookies of")
