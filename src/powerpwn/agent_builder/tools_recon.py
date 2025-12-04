#!/usr/bin/env python3
"""
Tools reconnaissance module for Agent Builder deployments.

This module queries Agent Builder chatbots to enumerate available tools, actions,
and integrations.
"""

import logging
import subprocess  # nosec B404 - Required for security toolset to execute Node.js scripts
from pathlib import Path
from typing import List, Optional

from powerpwn.cli.const import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

# ANSI Color Codes
COLOR_GREEN = "\033[92m"
COLOR_ORANGE = "\033[33m"
COLOR_RESET = "\033[0m"


class AgentBuilderToolsRecon:
    """
    Tools reconnaissance for Agent Builder chatbots.
    Queries chatbots to discover available tools and integrations.
    """

    def __init__(self, url_list: List[str], output_dir: str = "results"):
        """
        Initialize the tools recon scanner.

        Args:
            url_list: List of Agent Builder chatbot URLs to scan
            output_dir: Directory to save results (default: results/)
        """
        self.url_list = url_list
        self.output_dir = Path(output_dir)
        self.script_dir = Path(__file__).parent / "tools"
        self.query_script = self.script_dir / "query_agent_tools.js"

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up output file path for the JS script
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def check_dependencies(self) -> bool:
        """
        Check if required dependencies are installed.

        Returns:
            True if all dependencies are available, False otherwise
        """
        dependencies = ["node", "npm"]

        for dep in dependencies:
            if not self._command_exists(dep):
                logger.error(f"Required dependency '{dep}' not found.")
                logger.error("Please install Node.js and npm: https://nodejs.org/")
                return False

        # Check if query script exists
        if not self.query_script.exists():
            logger.error(f"Query script not found: {self.query_script}")
            return False

        # Check if node modules are installed
        package_json = self.script_dir.parent / "package.json"
        if not package_json.exists():
            logger.warning("package.json not found, will attempt to create it")
            self._create_package_json()

        node_modules = self.script_dir.parent / "node_modules"
        if not node_modules.exists() or not (node_modules / "puppeteer-extra").exists():
            logger.info("Installing Node.js dependencies...")
            if not self._install_node_modules():
                return False

        return True

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        from shutil import which

        return which(command) is not None

    def _create_package_json(self) -> None:
        """Create a package.json file with required dependencies."""
        package_json_content = """{
  "name": "agent-builder-tools-recon",
  "version": "1.0.0",
  "description": "Tools reconnaissance for Agent Builder chatbots",
  "main": "tools/query_agent_tools.js",
  "dependencies": {
    "puppeteer": "^23.0.0",
    "puppeteer-extra": "^3.3.6",
    "puppeteer-extra-plugin-stealth": "^2.11.2",
    "xlsx": "^0.18.5"
  }
}
"""
        package_json_path = self.script_dir.parent / "package.json"
        with open(package_json_path, "w") as f:
            f.write(package_json_content)
        logger.info(f"Created package.json at {package_json_path}")

    def _install_node_modules(self) -> bool:
        """Install Node.js dependencies using npm."""
        try:
            install_dir = self.script_dir.parent
            logger.info(f"Running npm install in {install_dir}...")

            result = subprocess.run(["npm", "install"], cwd=install_dir, capture_output=True, text=True, timeout=300)  # nosec B603 B607 - Hardcoded npm install command

            if result.returncode != 0:
                logger.error(f"npm install failed: {result.stderr}")
                return False

            logger.info("Node.js dependencies installed successfully")
            return True

        except subprocess.TimeoutExpired:
            logger.error("npm install timed out (5 minutes)")
            return False
        except Exception as e:
            logger.error(f"Error installing Node.js dependencies: {e}")
            return False

    def run_recon(self) -> bool:
        """
        Run tools reconnaissance on all URLs.

        Returns:
            True if scan completed successfully, False otherwise
        """
        if not self.check_dependencies():
            logger.error("Dependency check failed. Cannot proceed with scan.")
            return False

        total = len(self.url_list)
        logger.info("=" * 70)
        logger.info("🔍 Agent Builder Tools Reconnaissance")
        logger.info("=" * 70)
        logger.info(f"Total URLs to scan: {total}")
        logger.info(f"Output directory: {self.results_dir}")
        logger.info(f"Results file: {self.results_dir / 'agent_tools_output.xlsx'}")
        logger.info("=" * 70)

        success_count = 0
        error_count = 0

        for idx, url in enumerate(self.url_list, 1):
            logger.info(f"\n[{idx}/{total}] Scanning: {url}")

            try:
                result = self._query_chatbot(url)

                if result:
                    success_count += 1
                    logger.info(f"{COLOR_ORANGE}✓ Successfully queried {url}{COLOR_RESET}")
                else:
                    error_count += 1
                    logger.warning(f"✗ Failed to query {url}")

            except KeyboardInterrupt:
                logger.warning("\n👋 Scan interrupted by user.")
                logger.info(f"Progress: {idx}/{total} URLs scanned")
                logger.info(f"Results saved to: {self.results_dir / 'agent_tools_output.xlsx'}")
                return False
            except Exception as e:
                error_count += 1
                logger.error(f"✗ Error scanning {url}: {e}")

        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("📊 Scan Summary")
        logger.info("=" * 70)
        logger.info(f"Total URLs: {total}")
        if success_count > 0:
            logger.info(f"{COLOR_ORANGE}Successful: {success_count}{COLOR_RESET}")
        else:
            logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {error_count}")

        # Count agents with tools from this run only
        tools_count = self._count_agents_with_tools(self.url_list)
        if tools_count > 0:
            logger.info(f"{COLOR_GREEN}Agents with tools discovered: {tools_count}{COLOR_RESET}")
        else:
            logger.info(f"Agents with tools discovered: {tools_count}")

        logger.info(f"Results saved to: {self.results_dir / 'agent_tools_output.xlsx'}")
        logger.info("=" * 70)

        return error_count == 0

    def _query_chatbot(self, url: str) -> bool:
        """
        Query a single chatbot for tools information.

        Args:
            url: The chatbot URL to query

        Returns:
            True if query was successful, False otherwise
        """
        try:
            # Run the Node.js query script
            result = subprocess.run(  # nosec B603 B607 - Controlled script path, hardcoded node command
                ["node", str(self.query_script), url],
                cwd=self.script_dir.parent,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout per chatbot
            )

            # Print the output from the script
            if result.stdout:
                print(result.stdout, end="")

            if result.stderr:
                logger.warning(f"Script stderr: {result.stderr}")

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            logger.error(f"Query timed out for {url}")
            return False
        except Exception as e:
            logger.error(f"Error querying {url}: {e}")
            return False

    def _count_agents_with_tools(self, url_filter: Optional[List[str]] = None) -> int:
        """
        Count the number of agents that have tools discovered.

        Args:
            url_filter: Optional list of URLs to filter by. If provided, only counts tools for these URLs.

        Returns:
            Number of agents with tools (Has tools = 'True')
        """
        try:
            import openpyxl  # type: ignore

            excel_file = self.results_dir / "agent_tools_output.xlsx"
            if not excel_file.exists():
                return 0

            workbook = openpyxl.load_workbook(excel_file)
            sheet = workbook.active

            # Find the "Has tools" and "URL" columns
            has_tools_col = None
            url_col = None
            for idx, cell in enumerate(sheet[1], 1):
                if cell.value == "Has tools":
                    has_tools_col = idx
                elif cell.value == "URL":
                    url_col = idx

            if has_tools_col is None:
                return 0

            # Count rows where "Has tools" = "True"
            count = 0
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if len(row) >= has_tools_col and row[has_tools_col - 1] == "True":
                    # If URL filter is provided, only count if URL matches
                    if url_filter and url_col:
                        if len(row) >= url_col and row[url_col - 1] in url_filter:
                            count += 1
                    else:
                        count += 1

            return count

        except ImportError:
            # If openpyxl is not available, try pandas
            try:
                import pandas as pd  # type: ignore

                excel_file = self.results_dir / "agent_tools_output.xlsx"
                if not excel_file.exists():
                    return 0

                df = pd.read_excel(excel_file)
                if "Has tools" in df.columns:
                    tools_df = df[df["Has tools"] == "True"]

                    # If URL filter is provided, filter by URLs
                    if url_filter and "URL" in df.columns:
                        tools_df = tools_df[tools_df["URL"].isin(url_filter)]

                    return len(tools_df)
                return 0

            except Exception:
                return 0
        except Exception as e:
            logger.debug(f"Error counting agents with tools: {e}")
            return 0


def run_tools_recon_from_file(file_path: str) -> bool:
    """
    Run tools reconnaissance from a file containing URLs.

    Args:
        file_path: Path to file containing URLs (one per line)

    Returns:
        True if scan completed successfully, False otherwise
    """
    try:
        with open(file_path, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        if not urls:
            logger.error(f"No URLs found in {file_path}")
            return False

        logger.info(f"Loaded {len(urls)} URLs from {file_path}")

        recon = AgentBuilderToolsRecon(urls)
        return recon.run_recon()

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return False


def run_tools_recon_from_url(url: str) -> bool:
    """
    Run tools reconnaissance on a single URL.

    Args:
        url: The chatbot URL to scan

    Returns:
        True if scan completed successfully, False otherwise
    """
    recon = AgentBuilderToolsRecon([url])
    return recon.run_recon()
