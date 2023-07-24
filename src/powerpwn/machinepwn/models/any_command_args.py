from typing import Union

from pydantic import BaseModel, Field

from powerpwn.machinepwn.models.cleanup_command_args import CleanupCommandArgs
from powerpwn.machinepwn.models.code_exec_command_args import CodeExecCommandArgs
from powerpwn.machinepwn.models.exflirtate_file_command_args import ExflirtateFileCommandArgs
from powerpwn.machinepwn.models.ransomware_command_args import RansomwareCommandArgs
from powerpwn.machinepwn.models.steal_cookie_command_args import StealCookieCommandArgs
from powerpwn.machinepwn.models.steal_power_automate_token_command_args import StealPowerAutomateTokenCommandArgs


class AnyCommandArgs(BaseModel):
    __root__: Union[
        CleanupCommandArgs,
        CodeExecCommandArgs,
        RansomwareCommandArgs,
        ExflirtateFileCommandArgs,
        StealCookieCommandArgs,
        StealPowerAutomateTokenCommandArgs,
    ] = Field(discriminator="command_to_run")
