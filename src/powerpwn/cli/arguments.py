import argparse
from powerpwn.powerdump.utils.const import CACHE_PATH


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