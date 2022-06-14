import requests
import pydantic
from enum import Enum
from typing import Optional


class CommandType(Enum):
    PYTHON = "python"
    VISUALBASIC = "vb"
    JAVASCRIPT = "javascript"
    POWERSHELL = "powershell"


class RunType(Enum):
    attended = "attended"
    unattended = "unattended"
    empty = ""


class CommandResponse(pydantic.BaseModel):
    success: bool
    runType: RunType
    attendedError: str
    unattendedError: str
    scriptOutput: str
    scriptError: str


class PowerPwnClient:
    def __init__(self, url: str, sig: str):
        self.url = url
        self.params = {
            "api-version": "2016-06-01",
            "sp": "/triggers/manual/run",
            "sv": "1.0",
            "sig": sig
        }

    def run_command(self, command_type: CommandType, command: str) -> CommandResponse:
        resp = requests.post(
            url=self.url,
            params=self.params,
            json={
                "command": command,
                "commandType": command_type.value
            }
        )
        try:

            command_response = CommandResponse.parse_obj(resp.json())
            return command_response
        except pydantic.error_wrappers.ValidationError:
            print("Bad response. Raw content: {resp.content}")
            raise


    def run_python(self, command: str) -> CommandResponse:
        return self.run_command(command_type=CommandType.PYTHON, command=command)

    def run_visualbasic(self, command: str) -> CommandResponse:
        return self.run_command(command_type=CommandType.VISUALBASIC, command=command)

    def run_javascript(self, command: str) -> CommandResponse:
        return self.run_command(command_type=CommandType.JAVASCRIPT, command=command)

    def run_powershell(self, command: str) -> CommandResponse:
        return self.run_command(command_type=CommandType.POWERSHELL, command=command)
