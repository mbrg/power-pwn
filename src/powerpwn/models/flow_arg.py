from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class FlowToRunEnum(Enum):
    EXFILTRATION = "Exfil"
    RANSOMWARE = "Ransomware"
    CODE_EXEC = "CodeExec"
    CLEANUP = "Cleanup"


class CommandTypeEnum(Enum):
    PYTHON = "python"
    VISUALBASIC = "visualbasic"
    JAVASCRIPT = "javascript"
    POWERSHELL = "powershell"
    COMMANDLINE = "commandline"
    EMPTY = ""


class FlowArguments(BaseModel):
    FlowToRun: FlowToRunEnum
    ExfilTargetFile: str = Field(default="", help="Absolute path to file")
    RansomwareCrawlDepth: str = Field(default="", help="Number of recursive entries to sub-directories")
    RansomwareDirectoriesToInitCrawl: str = Field(default="", help="List of directories to crawl separated by a command. For example: 'C:\\,D:\\'")
    RansomwareEncryptionKey: str = Field(default="", help="AES256 encryption key")
    CodeExecCommandType: CommandTypeEnum = Field(default="", help="AES256 encryption key")
    CodeExecCommand: str = Field(default="", help="Command to execute")
