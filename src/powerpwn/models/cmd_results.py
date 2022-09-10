from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel, Field


class ExfiltrationOutputs(BaseModel):
    success: bool = Field(default=False)
    file_contents: str = Field(default="")


class RansomwareOutputs(BaseModel):
    files_found: int = Field(default=0)
    files_accessed: int = Field(default=0)
    files_processed: int = Field(default=0)
    errors: str = Field(default="")


class CodeExecOutputs(BaseModel):
    script_output: str = Field(default="")
    script_error: str = Field(default="")


class CleanupOutputs(BaseModel):
    log_files_found: int = Field(default=0)
    log_files_deleted: int = Field(default=0)


class StealCookieOutputs(BaseModel):
    cookies: str = Field(default="")


class StealPowerAutomateTokenOutputs(BaseModel):
    token: str = Field(default="")


class AgentRunType(Enum):
    attended = auto()
    unattended = auto()
    empty = ""


class AgentRunErrors(BaseModel):
    attended_run_error: dict
    unattended_run_error: dict


class CommandResults(BaseModel):
    is_success: bool
    agent_run_type: AgentRunType
    agent_run_errors: AgentRunErrors
    cmd_exfiltration: Optional[ExfiltrationOutputs]
    cmd_code_execution: Optional[CodeExecOutputs]
    cmd_ransomware: Optional[RansomwareOutputs]
    cmd_cleanup: Optional[CleanupOutputs]
    cmd_steal_cookie: Optional[StealCookieOutputs]
    cmd_steal_power_automate_token: Optional[StealPowerAutomateTokenOutputs]
