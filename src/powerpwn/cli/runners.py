from __future__ import annotations

import json
import logging
import os
import shutil

from powerpwn.agent_builder.agent_builder_scan import EndpointScanner, get_default_wordlist_path
from powerpwn.agent_builder.tools_recon import run_tools_recon_from_file, run_tools_recon_from_url
from powerpwn.cli.const import LOGGER_NAME
from powerpwn.common.cache.token_cache import TokenCache
from powerpwn.copilot.dump.dump import Dump
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.gui.gui import Gui as CopilotGui
from powerpwn.copilot.interactive_chat.interactive_chat import InteractiveChat
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.spearphishing.automated_spear_phisher import AutomatedSpearPhisher
from powerpwn.copilot.whoami.whoami import WhoAmI
from powerpwn.copilot_studio.modules.check_accessible import CheckAccessible
from powerpwn.copilot_studio.modules.deep_scan import DeepScan, get_tenant_id
from powerpwn.copilot_studio.modules.enum import Enum
from powerpwn.copilot_studio.modules.tools_recon import ToolsRecon
from powerpwn.nocodemalware.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.nocodemalware.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.nocodemalware.malware_runner import MalwareRunner
from powerpwn.powerdoor.backdoor_flow import BackdoorFlow
from powerpwn.powerdoor.enums.action_type import BackdoorActionType
from powerpwn.powerdoor.flow_factory_installer import FlowFlowInstaller
from powerpwn.powerdump.collect.data_collectors.data_collector import DataCollector
from powerpwn.powerdump.collect.mcp_recon import MCPRecon
from powerpwn.powerdump.collect.resources_collectors.resources_collector import ResourcesCollector
from powerpwn.powerdump.gui.gui import Gui
from powerpwn.powerdump.utils.auth import Auth, acquire_token, acquire_token_from_cached_refresh_token, get_cached_tenant
from powerpwn.powerdump.utils.const import API_HUB_SCOPE, POWER_APPS_SCOPE
from powerpwn.powerdump.utils.path_utils import collected_data_path, entities_path
from powerpwn.powerpages.powerpages import PowerPages
from powerpwn.powerphishing.app_installer import AppInstaller

logger = logging.getLogger(LOGGER_NAME)


def __init_command_token(args, scope: str) -> Auth:
    if args.clear_cache:
        TokenCache().clear_token_cache()
        return acquire_token(scope=scope, tenant=args.tenant)

    # if cached refresh token is found, use it
    if auth := acquire_token_from_cached_refresh_token(scope, args.tenant):
        return auth

    logger.info("Failed to acquire token from cached refresh token. Falling back to device-flow authentication to acquire new token.")

    return acquire_token(scope=scope, tenant=args.tenant)


def __clear_cache(cache_path):
    try:
        shutil.rmtree(cache_path)
    except FileNotFoundError:
        pass
    os.makedirs(cache_path, exist_ok=True)


def _get_scoped_cache_path(args, tenant) -> str:
    return os.path.join(args.cache_path, tenant)


def run_recon_command(args) -> str:
    auth = __init_command_token(args, POWER_APPS_SCOPE)

    # cache
    if args.clear_cache:
        __clear_cache(os.path.join(args.cache_path, os.path.join(auth.tenant, "resources")))

    scoped_cache_path = _get_scoped_cache_path(args, auth.tenant)
    entities_fetcher = ResourcesCollector(token=auth.token, cache_path=scoped_cache_path)
    entities_fetcher.collect_and_cache()

    logger.info(f"Recon is completed for tenant {auth.tenant} in {entities_path(scoped_cache_path)}")

    return auth.tenant


def run_gui_command(args) -> None:
    """
    Run local server for basic gui to show collected resources and data.
    tenant inference for data:
    1. if provided in args, use it
    2. try to get tenant from cached token and use it
    3. if only one tenant exist in cache path, use it
    4. otherwise, require tenant

    """
    scoped_cache_path: str | None = None
    if args.tenant:
        scoped_cache_path = _get_scoped_cache_path(args, args.tenant)
    elif cached_tenant := get_cached_tenant():
        scoped_cache_path = _get_scoped_cache_path(args, cached_tenant)
        logger.info(f"The cached tenant found is {cached_tenant}.")
    else:
        tenant_list = os.listdir(args.cache_path)
        if len(tenant_list) == 1:
            scoped_cache_path = _get_scoped_cache_path(args, tenant_list[0])
            logger.info(f"Only one tenant found in cache path. Using '{tenant_list[0]}' as tenant.")

    if not scoped_cache_path:
        logger.error("Tenant is not provided and it can not be found in cache. Please provide tenant id with -t flag.")
        return
    Gui().run(cache_path=scoped_cache_path)


def run_dump_command(args) -> str:
    if args.recon:
        run_recon_command(args)

    auth = __init_command_token(args, API_HUB_SCOPE)

    if args.clear_cache:
        __clear_cache(os.path.join(args.cache_path, os.path.join(auth.tenant, "data")))

    scoped_cache_path = _get_scoped_cache_path(args, auth.tenant)
    is_data_collected = DataCollector(token=auth.token, cache_path=scoped_cache_path).collect()
    if not is_data_collected:
        logger.info("No resources found to get data dump. Please make sure recon runs first or run dump command again with -r/--recon flag.")
    else:
        logger.info(f"Dump is completed for tenant {auth.tenant} in {collected_data_path(scoped_cache_path)}")

    return auth.tenant


def run_tenant_mcp_recon_command(args) -> None:
    """
    Run MCP recon to extract MCP server URLs from collected connector resources.
    Optionally probes discovered servers for capabilities.

    Workflow:
    1. Optionally run recon if -r/--recon flag is set
    2. Determine tenant ID from args or cached token
    3. Scan through collected connector resources
    4. Filter for MCP connectors and extract backend URLs
    5. Optionally probe discovered servers (default: True, skip with --no-probe)
    6. Save results to output file (JSON with probe data or TXT if no probe)
    """
    if args.recon:
        # Set default values for recon-specific arguments that may not exist in tenant-mcp-recon args
        if not hasattr(args, "clear_cache"):
            args.clear_cache = False
        if not hasattr(args, "gui"):
            args.gui = False

        tenant = run_recon_command(args)
    else:
        # Determine tenant for MCP scan
        if args.tenant:
            tenant = args.tenant
        elif cached_tenant := get_cached_tenant():
            tenant = cached_tenant
            logger.info(f"Using cached tenant: {tenant}")
        else:
            logger.error(
                "Tenant is not provided and cannot be found in cache. Please provide tenant id with -t flag or run with -r flag to perform recon first."
            )
            return

    scoped_cache_path = _get_scoped_cache_path(args, tenant)

    # Run MCP recon with optional probing
    probe_enabled = not args.no_probe  # Default is True (probe), unless --no-probe is set
    urls_only = args.urls_only  # Default is False (full JSON), unless --urls-only is set
    
    mcp_recon = MCPRecon(
        cache_path=scoped_cache_path,
        probe_timeout=args.timeout,
        max_concurrent_probes=args.max_concurrent,
    )
    output_file = mcp_recon.run(output_path=args.output, probe=probe_enabled, urls_only=urls_only)

    logger.info(f"MCP recon completed for tenant {tenant}. Results saved to: {output_file}")


def run_backdoor_flow_command(args):
    action_type = BackdoorActionType(args.backdoor_subcommand)
    if action_type == BackdoorActionType.delete_flow:
        backdoor_flow = BackdoorFlow(args.webhook_url)
        backdoor_flow.delete_flow(args.environment_id, args.flow_id)

    elif action_type == BackdoorActionType.create_flow:
        backdoor_flow = BackdoorFlow(args.webhook_url)
        backdoor_flow.create_flow_from_input_file(args.environment_id, args.input)

    elif action_type == BackdoorActionType.get_connections:
        backdoor_flow = BackdoorFlow(args.webhook_url)
        output_to_file = args.output and args.output != ""
        connections = backdoor_flow.get_connections(args.environment_id, not output_to_file)
        if output_to_file:
            f = open(args.output, "w+")
            f.write(json.dumps(connections, indent=4))
        else:
            logger.info(connections)

    elif action_type == BackdoorActionType.install_factory:
        auth = __init_command_token(args, POWER_APPS_SCOPE)
        FlowFlowInstaller(auth.token).install(args.environment_id, args.connection_id)


def run_nocodemalware_command(args):
    malware_runner = MalwareRunner(args.webhook_url)

    command_type = CommandToRunEnum(args.nocodemalware_subcommand)
    if command_type == CommandToRunEnum.CLEANUP:
        res = malware_runner.cleanup()
    elif command_type == CommandToRunEnum.CODE_EXEC:
        res = malware_runner.exec_command(args.command_to_execute, CodeExecTypeEnum(args.type))
    elif command_type == CommandToRunEnum.EXFILTRATION:
        res = malware_runner.exfiltrate(args.file)
    elif command_type == CommandToRunEnum.RANSOMWARE:
        res = malware_runner.ransomware(args.crawl_depth, args.dirs.split(","), args.encryption_key)
    elif command_type == CommandToRunEnum.STEAL_COOKIE:
        res = malware_runner.steal_cookie(args.cookie)
    elif command_type == CommandToRunEnum.STEAL_POWER_AUTOMATE_TOKEN:
        res = malware_runner.steal_power_automate_token()
    print(res)


def run_phishing_command(args):
    auth = __init_command_token(args, POWER_APPS_SCOPE)
    app_installer = AppInstaller(auth.token)
    if args.phishing_subcommand == "install-app":
        return app_installer.install_app(args.input, args.app_name, args.environment_id)
    elif args.phishing_subcommand == "share-app":
        return app_installer.share_app_with_org(args.app_id, args.environment_id, args.tenant)
    raise NotImplementedError("Phishing command has not been implemented yet.")


def run_copilot_chat_command(args):
    if args.copilot_subcommand == "gui":
        CopilotGui().run(args.directory)
        return

    parsed_args = ChatArguments(
        user=args.user,
        password=args.password,
        use_cached_access_token=args.cached_token,
        verbose=VerboseEnum(args.verbose),
        scenario=CopilotScenarioEnum(args.scenario),
    )

    if args.copilot_subcommand == "chat":
        InteractiveChat(parsed_args).start_chat()
        return
    elif args.copilot_subcommand == "spear-phishing":
        spear = AutomatedSpearPhisher(parsed_args)
        spear.phish()
        return
    elif args.copilot_subcommand == "whoami":
        whoami = WhoAmI(parsed_args)
        output_dir = whoami.execute()
        if args.gui:
            CopilotGui().run(output_dir)
        return

    elif args.copilot_subcommand == "dump":
        dump = Dump(parsed_args, args.directory)
        output_dir = dump.run()
        if args.gui:
            CopilotGui().run(output_dir)
        return

    raise NotImplementedError(f"Copilot {args.copilot_subcommand} subcommand has not been implemented yet.")


def run_get_tenant_command(args) -> None:
    """
    Retrieve Azure AD tenant ID from a domain name.
    
    Args:
        args: Command line arguments containing domain and optional timeout
    """
    domain = args.domain
    timeout = args.timeout
    
    logger.info(f"{'=' * 70}")
    logger.info(f"Retrieving Tenant ID for domain: {domain}")
    logger.info(f"{'=' * 70}")
    
    tenant_id = get_tenant_id(domain=domain, timeout=timeout)
    
    if tenant_id:
        logger.info(f"\n{'=' * 70}")
        logger.info(f"✓ Tenant ID found:")
        logger.info(f"  Domain: {domain}")
        logger.info(f"  Tenant ID: {tenant_id}")
        logger.info(f"{'=' * 70}")
        print(f"\n{tenant_id}")  # Print just the tenant ID for easy copying
    else:
        logger.error(f"\n{'=' * 70}")
        logger.error(f"✗ Failed to retrieve tenant ID for domain: {domain}")
        logger.error(f"{'=' * 70}")
        logger.error("Possible reasons:")
        logger.error("  - Domain does not have an Azure AD tenant")
        logger.error("  - Network connectivity issues")
        logger.error("  - Domain name is incorrect")


def run_copilot_studio_command(args):
    # copilot_studio_main.main(args)

    if args.copilot_studio_subcommand == "deep-scan":
        DeepScan(args)
        return
    elif args.copilot_studio_subcommand == "tools-recon":
        ToolsRecon(args)
        return
    elif args.copilot_studio_subcommand == "enum":
        Enum(args)
        return
    elif args.copilot_studio_subcommand == "get-tenant":
        run_get_tenant_command(args)
        return
    elif args.copilot_studio_subcommand == "check-accessible":
        CheckAccessible(args)
        return

    raise NotImplementedError("Copilot studio command has not been implemented yet.")


def run_powerpages_command(args):
    PowerPages(args)


def run_llm_hound_command(args):
    """
    Run LLM Hound to discover and probe AI integration surfaces (Claude/OpenAI APIs, MCP servers, LLM proxies)
    """
    import asyncio
    from datetime import datetime

    from powerpwn.llmhound.llmhound import LLMHound

    subcommand = args.llm_hound_subcommand

    if subcommand == "list-filters":
        # List available filters (doesn't require Shodan API)
        filters_file = getattr(args, "filters_file", None)

        # Load filters directly without initializing Shodan
        from pathlib import Path

        if filters_file is None:
            module_dir = Path(__file__).parent.parent / "llmhound"
            filters_file = module_dir / "discovery_filters.json"

        try:
            with open(filters_file, "r") as f:
                filters_data = json.load(f)

            logger.info("=" * 70)
            logger.info("Available LLM Hound Discovery Filters")
            logger.info("=" * 70)

            # Group by category
            for category_name, category_data in filters_data.get("filter_categories", {}).items():
                logger.info(f"\n{category_name.upper().replace('_', ' ')}")
                logger.info("-" * 70)

                for filter_def in category_data.get("filters", []):
                    logger.info(f"  {filter_def['name']}")
                    logger.info(f"    Description: {filter_def['description']}")
                    logger.info(f"    Tags: {', '.join(filter_def.get('tags', []))}")
                    logger.info(f"    Query: {filter_def['query']}")
                    logger.info("")

        except Exception as e:
            logger.error(f"Failed to load filters: {e}")
        return

    elif subcommand == "discover":
        # Discovery mode (with optional probing)

        # Get API key - check args, then env var, then prompt
        api_key = args.api_key

        # Try environment variable if not in args
        if not api_key:
            api_key = os.environ.get("SHODAN_API_KEY")
            if api_key:
                logger.info("Using Shodan API key from SHODAN_API_KEY environment variable")

        # Prompt if still not found
        if not api_key:
            import getpass

            logger.info("Shodan API key not provided via -k flag or SHODAN_API_KEY env var")
            logger.info("Please enter your Shodan API key (input will be hidden):")
            try:
                api_key = getpass.getpass("Shodan API Key: ")
                if not api_key or not api_key.strip():
                    logger.error("API key is required for discovery mode")
                    return
                api_key = api_key.strip()
            except KeyboardInterrupt:
                logger.info("\nOperation cancelled by user")
                return

        hunter = LLMHound(
            shodan_api_key=api_key,
            filters_file=getattr(args, "filters_file", None),
            probe_timeout=args.probe_timeout,
            max_concurrent_probes=args.max_concurrent,
        )

        # Determine output file
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filter_name = args.filter or args.category or "custom"
            extension = "txt" if args.urls_only else "json"
            output_file = f"llmhound_discovery_{filter_name}_{timestamp}.{extension}"

        # Run discovery
        try:
            results = asyncio.run(
                hunter.run_discovery_and_probe(
                    filter_name=getattr(args, "filter", None),
                    category=getattr(args, "category", None),
                    custom_query=getattr(args, "query", None),
                    max_results=args.max_results,
                    output_file=output_file,
                    probe=not args.no_probe,
                    urls_only=args.urls_only,
                )
            )

            # Print summary
            logger.info("\n" + "=" * 70)
            logger.info("Discovery Complete")
            logger.info("=" * 70)
            logger.info(f"Total discovered: {len(results.get('discovery', []))}")
            if not args.no_probe:
                logger.info(f"Total probed: {len(results.get('probe', []))}")
                accessible = len([r for r in results.get("probe", []) if r.get("accessible")])
                logger.info(f"Accessible servers: {accessible}")
            logger.info(f"Results saved to: {output_file}")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Discovery failed: {e}")

    elif subcommand == "probe":
        # Probe-only mode
        hunter = LLMHound(probe_timeout=args.timeout, max_concurrent_probes=args.max_concurrent)

        # Determine output file
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            if args.url:
                output_file = f"llmhound_probe_single_{timestamp}.json"
            else:
                output_file = f"llmhound_probe_results_{timestamp}.json"

        # Run probe
        try:
            if args.url:
                # Single URL probe
                results = asyncio.run(hunter.run_probe_single_url(server_url=args.url, output_file=output_file))
            else:
                # File-based probe
                results = asyncio.run(hunter.run_probe_only(server_list_file=args.input, output_file=output_file))

            # Print summary
            logger.info("\n" + "=" * 70)
            logger.info("Probe Complete")
            logger.info("=" * 70)
            logger.info(f"Total probed: {len(results)}")
            accessible = len([r for r in results if r.get("accessible")])
            logger.info(f"Accessible: {accessible}")
            logger.info(f"Results saved to: {output_file}")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Probe failed: {e}")

    elif args.llm_hound_subcommand == "mcp-registry-diving":
        # MCP Registry Diving: Discover from official MCP registry
        logger.info("Starting MCP Registry Diving...")

        # Initialize hunter
        hunter = LLMHound(probe_timeout=args.probe_timeout, max_concurrent_probes=args.max_concurrent)

        # Determine output file
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            extension = "txt" if args.urls_only else "json"
            output_file = f"llmhound_registry_diving_{timestamp}.{extension}"

        # Run registry diving
        probe = not args.no_probe
        try:
            results = asyncio.run(hunter.run_registry_diving(max_results=args.max_results, output_file=output_file, probe=probe, urls_only=args.urls_only))

            # Print summary
            logger.info("\n" + "=" * 70)
            logger.info("Registry Diving Complete")
            logger.info("=" * 70)
            logger.info(f"Total discovered: {results['metadata']['total_discovered']}")
            logger.info(f"Total probed: {results['metadata']['total_probed']}")
            logger.info(f"Results saved to: {output_file}")
            logger.info("=" * 70)

        except Exception as e:
            logger.error(f"Registry diving failed: {e}")
            import traceback

            traceback.print_exc()

    else:
        logger.error("Please specify a subcommand: list-filters, discover, probe, or mcp-registry-diving")
        logger.info("Run 'powerpwn llm-hound --help' for usage information")


def run_custom_gpt_hunter_command(args):
    """
    Run Custom GPT Hunter to discover and catalog Custom GPTs on ChatGPT.
    """
    import subprocess
    from pathlib import Path

    # Get the path to the custom_gpt_hunter module
    module_dir = Path(__file__).parent.parent / "custom_gpt_hunter"
    script_path = module_dir / "custom_gpt_hunter.js"

    # Check if Node.js is available
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Node.js is not installed or not in PATH.")
        logger.error("Please install Node.js from https://nodejs.org/ or using your package manager.")
        logger.error("  macOS: brew install node")
        logger.error("  Linux: sudo apt-get install nodejs")
        return

    # Check if npm packages are installed
    node_modules = module_dir / "node_modules"
    if not node_modules.exists():
        logger.error("npm packages are not installed.")
        logger.error(f"Please run: cd {module_dir} && npm install")
        return

    # Check if the script exists
    if not script_path.exists():
        logger.error(f"Custom GPT Hunter script not found at: {script_path}")
        return

    # Build the command
    cmd = ["node", str(script_path), args.search_query]

    if args.additional_pages > 0:
        cmd.append(str(args.additional_pages))

    logger.info(f"Starting Custom GPT Hunter...")
    logger.info(f"Search Query: {args.search_query}")
    logger.info(f"Additional Pages: {args.additional_pages} (Total: {args.additional_pages + 1} pages)")
    logger.info("")

    # Run the Node.js script
    try:
        subprocess.run(cmd, cwd=os.getcwd(), check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Custom GPT Hunter failed with exit code {e.returncode}")
    except KeyboardInterrupt:
        logger.info("\nCustom GPT Hunter interrupted by user.")
    except Exception as e:
        logger.error(f"Error running Custom GPT Hunter: {e}")


def run_agent_builder_scan_command(args):
    """
    Run agent builder hunter - handles both scan and tools-recon subcommands.
    """
    subcommand = getattr(args, "agent_builder_subcommand", None)

    if subcommand == "scan":
        run_agent_builder_scan(args)
    elif subcommand == "tools-recon":
        run_agent_builder_tools_recon(args)
    else:
        logger.error("Please specify a subcommand: 'scan' or 'tools-recon'")
        logger.info("Examples:")
        logger.info("  powerpwn agent-builder-hunter scan")
        logger.info("  powerpwn agent-builder-hunter tools-recon -f urls.txt")
        logger.info("  powerpwn agent-builder-hunter tools-recon -u https://example.vercel.app")


def run_agent_builder_scan(args):
    """
    Run agent builder scan to discover OpenAI Agent Builder deployments.
    """
    import glob
    from datetime import datetime
    from pathlib import Path

    # Validate arguments
    if hasattr(args, "timeout_per_endpoint") and args.timeout_per_endpoint and not args.timeout:
        logger.error("--timeout-per-endpoint requires --timeout to be specified.")
        return

    # Determine wordlist path
    wordlist_path = args.wordlist if args.wordlist else get_default_wordlist_path()

    # Check if wordlist exists
    if not os.path.exists(wordlist_path):
        logger.error(f"Wordlist not found: {wordlist_path}")
        logger.error("Please provide a valid wordlist with -w/--wordlist argument.")
        return

    # Handle reset flag
    if hasattr(args, "reset") and args.reset:
        logger.info("Resetting scan progress...")
        # Find and remove all progress files for this wordlist
        progress_pattern = f"{wordlist_path}.*.progress"
        progress_files = glob.glob(progress_pattern)

        if progress_files:
            for progress_file in progress_files:
                try:
                    os.remove(progress_file)
                    logger.info(f"Removed: {progress_file}")
                except Exception as e:
                    logger.error(f"Failed to remove {progress_file}: {e}")
            logger.info(f"Reset complete. Removed {len(progress_files)} progress file(s).")
        else:
            logger.info("No progress files found to reset.")

        # Don't exit - continue with the scan
        logger.info("Starting fresh scan...")

    # Determine output file
    if hasattr(args, "output") and args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"found_agent_builder_deployments_{timestamp}.txt"

    logger.info("Starting Agent Builder Hunter...")
    logger.info(f"Wordlist: {wordlist_path}")

    # Create and run scanner
    scanner = EndpointScanner(
        wordlist_path=wordlist_path,
        output_file=output_file,
        custom_endpoint=None,
        skip_defaults=False,
        run_duration=args.run_duration,
        pause_duration=args.pause_duration,
        rate=args.rate,
        threads=args.threads,
        filter_codes=args.filter_codes,
        timeout=getattr(args, "timeout", None),
        timeout_per_endpoint=getattr(args, "timeout_per_endpoint", False),
    )

    scanner.run()


def run_agent_builder_tools_recon(args):
    """
    Run tools reconnaissance on Agent Builder chatbots.
    """
    # Validate arguments
    if not args.url and not args.file:
        logger.error("Please provide either -u/--url or -f/--file argument.")
        logger.info("Examples:")
        logger.info("  powerpwn agent-builder-hunter tools-recon -f urls.txt")
        logger.info("  powerpwn agent-builder-hunter tools-recon -u https://example.vercel.app")
        return

    if args.url and args.file:
        logger.error("Please provide either -u/--url OR -f/--file, not both.")
        return

    try:
        if args.file:
            logger.info(f"Running tools reconnaissance from file: {args.file}")
            success = run_tools_recon_from_file(args.file)
        else:
            logger.info(f"Running tools reconnaissance on: {args.url}")
            success = run_tools_recon_from_url(args.url)

        if success:
            logger.info("✓ Tools reconnaissance completed successfully")
        else:
            logger.warning("⚠ Tools reconnaissance completed with errors")

    except Exception as e:
        logger.error(f"Error running tools reconnaissance: {e}")
