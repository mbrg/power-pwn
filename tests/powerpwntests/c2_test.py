from powerpwn.c2 import PowerPwnC2
from powerpwn.models.cmd_arguments import CommandArguments, CommandToRunEnum
from powerpwn.models.cmd_results import (
    AgentRunErrors,
    AgentRunType,
    CleanupOutputs,
    CodeExecOutputs,
    CommandResults,
    ExfiltrationOutputs,
    RansomwareOutputs,
    StealCookieOutputs,
    StealPowerAutomateTokenOutputs,
)


class DummyPowerPwnC2(PowerPwnC2):
    def _run_cmd(self, arguments_as_dict: dict) -> dict:
        command_to_run_arg_name = CommandArguments.command_to_run.__name__
        command_to_run_val = arguments_as_dict[command_to_run_arg_name]

        cmd_res = CommandResults.construct(
            is_success=True,
            agent_run_type=AgentRunType.attended.value,
            agent_run_errors=AgentRunErrors.construct(attended_run_error={}, unattended_run_error={}),
        )

        if command_to_run_val == CommandToRunEnum.CODE_EXEC.value:
            cmd_res.cmd_code_execution = CodeExecOutputs.construct()
        elif command_to_run_val == CommandToRunEnum.RANSOMWARE.value:
            cmd_res.cmd_ransomware = RansomwareOutputs.construct()
        elif command_to_run_val == CommandToRunEnum.EXFILTRATION.value:
            cmd_res.cmd_exfiltration = ExfiltrationOutputs.construct()
        elif command_to_run_val == CommandToRunEnum.CLEANUP.value:
            cmd_res.cmd_cleanup = CleanupOutputs.construct()
        elif command_to_run_val == CommandToRunEnum.STEAL_POWER_AUTOMATE_TOKEN.value:
            cmd_res.cmd_steal_power_automate_token = StealPowerAutomateTokenOutputs.construct()
        elif command_to_run_val == CommandToRunEnum.STEAL_COOKIE.value:
            cmd_res.cmd_steal_cookie = StealCookieOutputs.construct()
        else:
            raise ValueError(f"command_to_run has invalid value: {command_to_run_val}.")

        return cmd_res.json()
