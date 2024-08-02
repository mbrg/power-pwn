import argparse
import logging

from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.nocodemalware.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.powerdoor.enums.action_type import BackdoorActionType
from powerpwn.powerdump.utils.const import CACHE_PATH


def module_gui(sub_parser: argparse.ArgumentParser):
    gui_parser = sub_parser.add_parser(
        "gui",
        description="Show collected resources and data.",
        help="Show collected resources and data via GUI.",
    )
    gui_parser.add_argument(
        "--cache-path", default=CACHE_PATH, type=str, help="Path to cached resources."
    )
    gui_parser.add_argument(
        "-t", "--tenant", required=False, type=str, help="Tenant id to launch gui."
    )


def module_dump(sub_parser: argparse.ArgumentParser):
    dump_parser = sub_parser.add_parser(
        "dump",
        description="Dump content for all available connection from recon",
        help="Dump content for all available connection from recon",
    )
    dump_parser.add_argument(
        "-c", "--clear-cache", action="store_true", help="Clear local disk cache"
    )
    dump_parser.add_argument(
        "--cache-path",
        default=CACHE_PATH,
        help="Path to store collected resources and data.",
    )
    dump_parser.add_argument(
        "-t", "--tenant", required=False, type=str, help="Tenant id to connect."
    )
    dump_parser.add_argument(
        "-g", "--gui", action="store_true", help="Run local server for gui."
    )
    dump_parser.add_argument(
        "-r",
        "--recon",
        action="store_true",
        help="Run recon before dump. Should be used if recon command was not run before.",
    )


def module_recon(sub_parser: argparse.ArgumentParser):
    dump_parser = sub_parser.add_parser(
        "recon",
        description="Recon for available data connections",
        help="Recon for available data connections.",
    )
    dump_parser.add_argument(
        "-c", "--clear-cache", action="store_true", help="Clear local disk cache"
    )
    dump_parser.add_argument(
        "--cache-path",
        default=CACHE_PATH,
        help="Path to store collected resources and data.",
    )
    dump_parser.add_argument(
        "-t", "--tenant", required=False, type=str, help="Tenant id to connect."
    )
    dump_parser.add_argument(
        "-g", "--gui", action="store_true", help="Run local server for gui."
    )


def module_nocodemalware(command_subparsers: argparse.ArgumentParser):
    nocodemalware_parser = command_subparsers.add_parser(
        "nocodemalware",
        description="Repurpose trusted execs, service accounts and cloud services to power a malware operation",
        help="Repurpose trusted execs, service accounts and cloud services to power a malware operation.",
    )
    nocodemalware_parser.add_argument(
        "-w",
        "--webhook-url",
        required=True,
        type=str,
        help="Webhook url to the flow factory installed in powerplatform",
    )
    nocodemalware_parser = nocodemalware_parser.add_subparsers(
        help="nocodemalware_subcommand", dest="nocodemalware_subcommand"
    )

    module_nocodemalware_subcommand_exec(nocodemalware_parser)


def module_nocodemalware_subcommand_exec(command_subparsers: argparse.ArgumentParser):
    steal_fqdn_parser = command_subparsers.add_parser(
        "steal-cookie", description="Steal cookie of fqdn"
    )
    steal_fqdn_parser.add_argument(
        "--fqdn",
        required=True,
        type=str,
        help="Fully qualified domain name to fetch the cookies of",
    )

    command_subparsers.add_parser(
        "steal-power-automate-token", description="Steal power automate token"
    )

    execute_command_parser = command_subparsers.add_parser(
        "command-exec", description="Execute command on machine"
    )
    execute_command_parser.add_argument(
        "-t",
        "--type",
        required=True,
        type=str,
        choices=[cmd_type.value for cmd_type in CodeExecTypeEnum],
        help="Command type",
    )
    execute_command_parser.add_argument(
        "-c", "--command-to-execute", required=True, type=str, help="Command to execute"
    )

    ransomware_parser = command_subparsers.add_parser(
        "ransomware", description="Ransomware"
    )
    ransomware_parser.add_argument(
        "--crawl_depth",
        required=True,
        type=str,
        help="Recursively search into subdirectories this many times",
    )
    ransomware_parser.add_argument(
        "-k",
        "--encryption-key",
        required=True,
        type=str,
        help="an encryption key used to encrypt each file identified (AES256)",
    )
    ransomware_parser.add_argument(
        "--dirs",
        required=True,
        type=str,
        help="A list of directories to begin crawl from separated by a comma (e.g.'C:\\,D:\\')",
    )

    exfiltrate_file_parser = command_subparsers.add_parser(
        "exfiltrate", description="Exfiltrate file"
    )
    exfiltrate_file_parser.add_argument(
        "-f", "--file", required=True, type=str, help="Absolute path to file"
    )

    command_subparsers.add_parser("cleanup", description="Cleanup")


def module_backdoor(command_subparsers: argparse.ArgumentParser):
    backdoor_parser = command_subparsers.add_parser(
        "backdoor",
        description="Install a backdoor on the target tenant.",
        help="Install a backdoor on the target tenant",
    )
    backdoor_parser.add_argument(
        "-e",
        "--environment-id",
        required=True,
        type=str,
        help="Environment id in powerplatform.",
    )
    backdoor_subparsers = backdoor_parser.add_subparsers(
        help="backdoor_subcommand", dest="backdoor_subcommand"
    )

    ## Delete Flow parser ##
    delete_flow_parser = backdoor_subparsers.add_parser(
        BackdoorActionType.delete_flow.value,
        description="Deletes flow.",
        help="Deletes flow using installed backdoor flow.",
    )
    delete_flow_parser.add_argument(
        "-w",
        "--webhook-url",
        required=True,
        type=str,
        help="Webhook url to the flow factory installed in powerplatform",
    )
    delete_flow_parser.add_argument(
        "-f", "--flow-id", type=str, help="Flow id to delete."
    )

    ## Create Flow parser ##
    create_flow_parser = backdoor_subparsers.add_parser(
        BackdoorActionType.create_flow.value,
        description="Creates a flow.",
        help="Creates a flow using installed backdoor flow.",
    )
    create_flow_parser.add_argument(
        "-w",
        "--webhook-url",
        required=True,
        type=str,
        help="Webhook url to the flow factory installed in powerplatform",
    )
    create_flow_parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to flow details input file.",
    )

    ## Get connections parser ##
    get_connections_parser = backdoor_subparsers.add_parser(
        BackdoorActionType.get_connections.value,
        description="Get connections",
        help="Gets connections details in environment",
    )
    get_connections_parser.add_argument(
        "-w",
        "--webhook-url",
        required=True,
        type=str,
        help="Webhook url to the flow factory installed in powerplatform",
    )
    get_connections_parser.add_argument(
        "-o", "--output", type=str, default="", help="Path to output file."
    )

    ## backdoor installer parser ##
    installer = backdoor_subparsers.add_parser(
        BackdoorActionType.install_factory.value,
        description="Install flow factory",
        help="Installs flow factory in powerplatform",
    )
    installer.add_argument(
        "-c",
        "--connection-id",
        required=True,
        type=str,
        help="The connection id of management connection",
    )
    installer.add_argument(
        "-t", "--tenant", required=False, type=str, help="Tenant id to connect."
    )


def module_phishing(command_subparsers: argparse.ArgumentParser):
    phishing = command_subparsers.add_parser(
        "phishing",
        description="Deploy a trustworthy phishing app",
        help="Deploy a trustworthy phishing app.",
    )
    phishing_subparsers = phishing.add_subparsers(
        help="phishing_subcommand", dest="phishing_subcommand"
    )

    installer = phishing_subparsers.add_parser(
        "install-app",
        description="Installs phishing app.",
        help="Installs a phishing app in the target environment.",
    )
    installer.add_argument(
        "-i", "--input", type=str, required=True, help="Path to app package zip file."
    )
    installer.add_argument(
        "-t", "--tenant", required=False, type=str, help="Tenant id to connect."
    )
    installer.add_argument(
        "-n", "--app-name", required=True, type=str, help="Display name of the app."
    )
    installer.add_argument(
        "-e",
        "--environment-id",
        required=True,
        type=str,
        help="Environment id to install the app in.",
    )

    app_share = phishing_subparsers.add_parser(
        "share-app",
        description="Share app with organization",
        help="Share app with organization",
    )
    app_share.add_argument(
        "-a", "--app-id", required=True, type=str, help="App id to share"
    )
    app_share.add_argument(
        "-e",
        "--environment-id",
        required=True,
        type=str,
        help="Environment id that the app belongs to.",
    )
    app_share.add_argument(
        "-t", "--tenant", required=True, type=str, help="Tenant id to connect."
    )


def module_copilot(command_subparsers: argparse.ArgumentParser):
    copilot = command_subparsers.add_parser(
        "copilot",
        description="Connects and interacts with copilot.",
        help="Connects and interacts with copilot.",
    )
    copilot_subparsers = copilot.add_subparsers(
        help="copilot_subcommand", dest="copilot_subcommand"
    )

    interactive_chat = copilot_subparsers.add_parser(
        "chat",
        description="Starts an interactive chat with copilot",
        help="Connects to copilot and starts an interactive chat session.",
    )
    copilot_modules(interactive_chat)

    spearphishing = copilot_subparsers.add_parser(
        "spear-phishing",
        description="Starts a spearphishing using copilot",
        help="Targets a compromised user's collaborators and crafts personalized emails using copilot",
    )
    copilot_modules(spearphishing)


def copilot_modules(parser):
    parser.add_argument(
        "-u", "--user", required=True, type=str, help="User email to connect."
    )
    parser.add_argument(
        "-p", "--password", required=False, type=str, help="User password to connect."
    )
    parser.add_argument(
        "--cached-token",
        action="store_true",
        help="Use cached access token to connect to copilot if exists.",
    )
    parser.add_argument(
        "-s",
        "--scenario",
        required=True,
        type=str,
        choices=[scenario_type.value for scenario_type in CopilotScenarioEnum],
        help="Scenario to run.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        required=False,
        type=str,
        default=VerboseEnum.off.value,
        choices=[verbose_level.value for verbose_level in VerboseEnum],
        help="Verbose level. Default is off.",
    )


def module_copilot_studio(command_subparsers: argparse.ArgumentParser):
    copilot = command_subparsers.add_parser(
        "copilot-studio-hunter",
        description="Scan, enumerate and recon Copilot Studio bots.",
        help="Scan, enumerate and recon Copilot Studio bots.",
    )
    copilot_subparsers = copilot.add_subparsers(
        help="copilot_studio_subcommand", dest="copilot_studio_subcommand"
    )

    deep_scan = copilot_subparsers.add_parser(
        "deep-scan",
        description="Starts a recon deep scan based on a domain or tenant. Requires FFUF to be installed.",
        help="Starts a recon deep scan based on a domain or tenant. Requires FFUF to be installed.",
    )
    copilot_studio_modules(deep_scan, "deep-scan")

    enum = copilot_subparsers.add_parser(
        "enum",
        description="Starts enumerating for Azure tenant IDs or environments IDs.  Requires AMASS to be installed.",
        help="Starts enumerating for Azure tenant IDs or environments IDs. Requires AMASS to be installed.",
    )
    copilot_studio_modules(enum, "enum")


def copilot_studio_modules(parser: argparse.ArgumentParser, module: str):

    if module == "deep-scan":
        parser.add_argument(
            "-r",
            "--rate",
            type=int,
            default=0,
            help="Rate limit in seconds between ffuf requests",
        )
        parser.add_argument(
            "-t",
            "--threads",
            type=int,
            default=40,
            help="Number of concurrent ffuf threads",
        )
        parser.add_argument(
            "--mode",
            choices=["verbose", "silent"],
            default="-s",
            help="Choose between verbose (-v) and silent (-s) mode for ffuf.",
        )
        parser.add_argument(
            "-tp",
            "--timeout_prefix",
            help="The timeout for the solution prefix scan to have (in seconds)",
            default=300,
        )
        parser.add_argument(
            "-tb",
            "--timeout_bots",
            help="The timeout for each of the bot scans (one-word/two-word/three-word) to have (in seconds)",
            default=300,
        )

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-d",
            "--domain",
            type=str,
            help="The domain to query for tenant ID and run ffuf on",
        )
        group.add_argument(
            "-i", "--tenant-id", type=str, help="The tenant ID to run FFUF on"
        )

    if module == "enum":
        parser.add_argument(
            "-e",
            "--enumerate",
            choices=["environment", "tenant"],
            help="Run the enumeration function on environment or tenant",
        )
        parser.add_argument(
            "-t",
            "--timeout",
            help="The timeout for the enumeration process to have (in seconds)",
            default=300,
        )


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--log-level",
        default=logging.INFO,
        type=lambda x: getattr(logging, x),
        help="Configure the logging level.",
    )
    command_subparsers = parser.add_subparsers(help="command", dest="command")

    module_dump(command_subparsers)
    module_recon(command_subparsers)
    module_gui(command_subparsers)
    module_backdoor(command_subparsers)
    module_nocodemalware(command_subparsers)
    module_phishing(command_subparsers)
    module_copilot(command_subparsers)
    module_copilot_studio(command_subparsers)

    args = parser.parse_args()

    return args
