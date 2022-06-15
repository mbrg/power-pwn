import requests
import pydantic
from enum import Enum


class CommandType(Enum):
    PYTHON = "python"
    VISUALBASIC = "vb"
    JAVASCRIPT = "javascript"
    POWERSHELL = "powershell"


class RunType(Enum):
    attended = "attended"
    unattended = "unattended"
    empty = ""


class RunErrors(pydantic.BaseModel):
    attendedRunError: dict
    unattendedRunError: dict


class CommandResponse(pydantic.BaseModel):
    runSuccess: bool
    runType: RunType
    runErrors: RunErrors
    scriptOutput: str
    scriptError: str


class PowerPwnClient:
    def __init__(self, post_url: str):
        self.post_url = post_url

    def run_command(self, command_type: CommandType, command: str) -> CommandResponse:
        resp = requests.post(
            url=self.post_url,
            json={
                "command": command,
                "commandType": command_type.value
            }
        )
        try:

            command_response = CommandResponse.parse_obj(resp.json())
            return command_response
        except pydantic.error_wrappers.ValidationError:
            print(f"Bad response. Raw content: {resp.content}")
            raise


    def run_python2(self, command: str) -> CommandResponse:
        return self.run_command(command_type=CommandType.PYTHON, command=command)

    def run_visualbasic(self, command: str) -> CommandResponse:
        return self.run_command(command_type=CommandType.VISUALBASIC, command=command)

    def run_javascript(self, command: str) -> CommandResponse:
        return self.run_command(command_type=CommandType.JAVASCRIPT, command=command)

    def run_powershell(self, command: str) -> CommandResponse:
        return self.run_command(command_type=CommandType.POWERSHELL, command=command)
