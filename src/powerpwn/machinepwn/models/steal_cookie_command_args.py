from typing import Literal

from powerpwn.machinepwn.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.machinepwn.models.cmd_arguments import CommandArguments
from powerpwn.machinepwn.models.steal_cookie_args_properties import StealCookieArgsProperties


class StealCookieCommandArgs(CommandArguments[StealCookieArgsProperties]):
    command_to_run: Literal[
        CommandToRunEnum.STEAL_COOKIE
    ] = CommandToRunEnum.STEAL_COOKIE
