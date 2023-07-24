from typing import Literal

from powerpwn.machinepwn.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.machinepwn.models.cmd_arguments import CommandArguments
from powerpwn.machinepwn.models.ransomware_args_properties import (
    RansomwareArgsProperties,
)


class RansomwareCommandArgs(CommandArguments[RansomwareArgsProperties]):
    command_to_run: Literal[CommandToRunEnum.RANSOMWARE] = CommandToRunEnum.RANSOMWARE
