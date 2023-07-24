from typing import Literal

from powerpwn.machinepwn.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.machinepwn.models.cmd_arguments import CommandArguments
from powerpwn.machinepwn.models.code_exec_args_properties import CodeExecArgsProperties


class CodeExecCommandArgs(CommandArguments[CodeExecArgsProperties]):
    command_to_run: Literal[CommandToRunEnum.CODE_EXEC] = CommandToRunEnum.CODE_EXEC
