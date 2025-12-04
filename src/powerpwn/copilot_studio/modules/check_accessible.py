"""
Module for checking accessibility of Copilot Studio bots and optionally checking for knowledge sources.
"""

import logging
import os
import subprocess  # nosec B404 - Required for security toolset to execute Node.js validation scripts
from typing import List

from powerpwn.copilot_studio.modules.deep_scan import get_project_file_path, sort_unique_values_in_file

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

logger = logging.getLogger(__name__)


class CheckAccessible:
    """
    Check if Copilot Studio bots are accessible and optionally test for knowledge sources.
    """

    def __init__(self, args):
        """
        Initialize the CheckAccessible class.

        :param args: Command line arguments
        """
        self.args = args
        self.bot_urls: List[str] = []
        self.accessible_bots: List[str] = []

        # Collect bot URLs from either single URL or file
        if args.url:
            self.bot_urls = [args.url]
        elif args.input_file:
            if not os.path.exists(args.input_file):
                logger.error(f"Input file not found: {args.input_file}")
                print(f"{RED}Error: Input file not found: {args.input_file}{RESET}")
                return

            with open(args.input_file, "r") as f:
                self.bot_urls = [line.strip() for line in f if line.strip()]

        if not self.bot_urls:
            logger.error("No bot URLs provided")
            print(f"{RED}Error: No bot URLs provided{RESET}")
            return

        print(f"\n{GREEN}Starting accessibility check for {len(self.bot_urls)} bot(s)...{RESET}\n")

        # Check accessibility
        self._check_bot_accessibility()

        # Optionally check for knowledge sources
        if args.check_knowledge and self.accessible_bots:
            print(f"\n{GREEN}Checking accessible bots for knowledge sources...{RESET}\n")
            self._check_knowledge_sources()

    def _check_bot_accessibility(self):
        """
        Check if bots are accessible using the cross-platform is_chat_live script.
        """
        # Use the cross-platform script (supports Windows, macOS, and Linux)
        pup_path = get_project_file_path("tools/pup_is_webchat_live", "is_chat_live.js")

        # Prepare output file
        open_bots_path = get_project_file_path("final_results/", "chat_exists_output.txt")
        with open(open_bots_path, "w") as _:
            pass  # Empty the file

        # Check each bot
        for bot_url in self.bot_urls:
            try:
                command = f"node {pup_path} {bot_url}"
                logging.debug(f"Running command: `{command}`")
                subprocess.run(command, shell=True, check=True)  # nosec
            except subprocess.CalledProcessError as e:
                logging.error(f"Error occurred while checking bot accessibility: {e}")

        # Collect accessible bots
        if os.path.exists(open_bots_path):
            self.accessible_bots = sort_unique_values_in_file(open_bots_path)

        # Print summary
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}Accessibility Check Summary:{RESET}")
        print(f"{GREEN}  Total bots checked: {len(self.bot_urls)}{RESET}")
        print(f"{GREEN}  Accessible bots: {len(self.accessible_bots)}{RESET}")
        print(f"{GREEN}  Results saved to: {open_bots_path}{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")

    def _check_knowledge_sources(self):
        """
        Check accessible bots for knowledge sources using query_chat.js.
        """
        pup_path = get_project_file_path("tools/pup_query_webchat", "query_chat.js")
        knowledge_output_path = get_project_file_path("final_results/", "extracted_knowledge.xlsx")

        # Delete existing Excel file to start fresh
        if os.path.exists(knowledge_output_path):
            os.remove(knowledge_output_path)
            logging.debug(f"Deleted existing file: {knowledge_output_path}")

        # Check each accessible bot
        for bot_url in self.accessible_bots:
            try:
                command = f"node {pup_path} {bot_url}"
                logging.debug(f"Running command: `{command}`")
                subprocess.run(command, shell=True, check=True)  # nosec
            except subprocess.CalledProcessError as e:
                logging.error(f"Error occurred while checking knowledge sources: {e}")

        # Print summary
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}Knowledge Sources Check Summary:{RESET}")
        print(f"{GREEN}  Checked {len(self.accessible_bots)} accessible bot(s){RESET}")
        print(f"{GREEN}  Results saved to: {knowledge_output_path}{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
