from pydantic import BaseModel
from enum import Enum


class ExfiltrationOutputs(BaseModel):
    Success: bool
    FileContents: str


class RansomwareOutputs(BaseModel):
    FilesFound: int
    FilesAccessed: int
    FilesProcessed: int


class CodeExecOutputs(BaseModel):
    scriptOutput: str
    scriptError: str


class CleanupOutputs(BaseModel):
    FilesFound: int
    LogFilesDeleted: int


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
