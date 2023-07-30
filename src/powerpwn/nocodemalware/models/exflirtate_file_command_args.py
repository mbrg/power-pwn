from typing import Literal

from powerpwn.machinepwn.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.machinepwn.models.cmd_arguments import CommandArguments
from powerpwn.machinepwn.models.exflirtate_file_args_properties import ExflirtateFileArgsProperties


class ExflirtateFileCommandArgs(CommandArguments[ExflirtateFileArgsProperties]):
    command_to_run: Literal[CommandToRunEnum.EXFILTRATION] = CommandToRunEnum.EXFILTRATION
