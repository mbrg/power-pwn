import logging

from art import tprint  # type: ignore

from powerpwn.cli.arguments import parse_arguments
from powerpwn.cli.const import LOGGER_NAME
from powerpwn.cli.runners import (
    run_agent_builder_scan_command,
    run_backdoor_flow_command,
    run_copilot_chat_command,
    run_copilot_studio_command,
    run_custom_gpt_hunter_command,
    run_dump_command,
    run_gui_command,
    run_llm_hound_command,
    run_nocodemalware_command,
    run_phishing_command,
    run_powerpages_command,
    run_recon_command,
    run_tenant_mcp_recon_command,
)

logger = logging.getLogger(LOGGER_NAME)


def main():
    print("\n\n------------------------------------------------------------")
    tprint("powerpwn")
    print("Black Hat Europe 2025 Arsenal edition\n\n")
    print("------------------------------------------------------------\n")

    args = parse_arguments()

    logging.basicConfig(level=args.log_level, format="%(asctime)s | %(name)s | %(levelname)s |  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    logger.level = args.log_level
    command = args.command

    if command == "dump":
        run_dump_command(args)
        if args.gui:
            logger.info("Going to run local server for gui")
            run_gui_command(args)
    elif command == "recon":
        run_recon_command(args)
        if args.gui:
            logger.info("Going to run local server for gui")
            run_gui_command(args)
    elif command == "tenant-mcp-recon":
        run_tenant_mcp_recon_command(args)
    elif command == "gui":
        run_gui_command(args)
    elif command == "backdoor":
        run_backdoor_flow_command(args)
    elif command == "nocodemalware":
        run_nocodemalware_command(args)
    elif command == "phishing":
        run_phishing_command(args)
    elif command == "copilot":
        run_copilot_chat_command(args)
    elif command == "copilot-studio-hunter":
        run_copilot_studio_command(args)
    elif command == "powerpages":
        run_powerpages_command(args)
    elif command == "llm-hound":
        run_llm_hound_command(args)
    elif command == "custom-gpt-hunter":
        run_custom_gpt_hunter_command(args)
    elif command == "agent-builder-hunter":
        run_agent_builder_scan_command(args)
    else:
        logger.info("Run `powerpwn --help` for available commands.")


if __name__ == "__main__":
    main()
