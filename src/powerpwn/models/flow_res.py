from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class ExfiltrationOutputs(BaseModel):
    Success: bool = Field(default=False)
    FileContents: str = Field(default="")


class RansomwareOutputs(BaseModel):
    FilesFound: int = Field(default=0)
    FilesAccessed: int = Field(default=0)
    FilesProcessed: int = Field(default=0)
    Errors: str = Field(default="")


class CodeExecOutputs(BaseModel):
    ScriptOutput: str = Field(default="")
    ScriptError: str = Field(default="")


class CleanupOutputs(BaseModel):
    FilesFound: int = Field(default=0)
    LogFilesDeleted: int = Field(default=0)


class StealCookieOutputs(BaseModel):
    Cookie: str = Field(default="")


class StealPowerAutomateTokenOutputs(BaseModel):
    Token: str = Field(default="")


class RunType(Enum):
    attended = "attended"
    unattended = "unattended"
    empty = ""


class RunErrors(BaseModel):
    AttendedRunError: dict
    UnattendedRunError: dict


class FlowResults(BaseModel):
    FlowSuccess: bool
    FlowType: RunType
    FlowErrors: RunErrors
    Cleanup: Optional[CleanupOutputs]
    Exfil: Optional[ExfiltrationOutputs]
    CodeExec: Optional[CodeExecOutputs]
    Ransomware: Optional[RansomwareOutputs]
    StealCookie: Optional[StealCookieOutputs]
    StealPowerAutomateToken: Optional[StealPowerAutomateTokenOutputs]
