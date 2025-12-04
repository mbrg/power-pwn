import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.powerdump.utils.path_utils import entities_path

logger = logging.getLogger(LOGGER_NAME)

# ANSI Color Codes
COLOR_GREEN = "\033[92m"
COLOR_RESET = "\033[0m"


class MCPRecon:
    """
    A class to scan collected connector resources and extract MCP server URLs.
    Optionally probes discovered servers for capabilities.
    """

    def __init__(self, cache_path: str, probe_timeout: int = 15, max_concurrent_probes: int = 5) -> None:
        """
        Initialize MCP Recon.

        Args:
            cache_path: Path to cached resources
            probe_timeout: Timeout for probing servers in seconds
            max_concurrent_probes: Maximum concurrent probe connections
        """
        self.__cache_path = cache_path
        self.__probe_timeout = probe_timeout
        self.__max_concurrent_probes = max_concurrent_probes

    def extract_mcp_servers(self) -> List[str]:
        """
        Scan through all collected connectors and extract MCP server backend URLs.

        Returns:
            List of MCP server URLs
        """
        mcp_servers: List[str] = []
        resources_path = entities_path(self.__cache_path)

        if not os.path.exists(resources_path):
            logger.error(f"Resources path does not exist: {resources_path}")
            logger.error("Please run recon command first to collect connector information.")
            return mcp_servers

        # Iterate through all environments
        for env_name in os.listdir(resources_path):
            env_path = os.path.join(resources_path, env_name)
            if not os.path.isdir(env_path):
                continue

            connector_path = os.path.join(env_path, "connector")
            if not os.path.exists(connector_path):
                logger.warning(f"No connector directory found in environment: {env_name}")
                continue

            # Iterate through all connector JSON files
            for connector_file in os.listdir(connector_path):
                if not connector_file.endswith(".json"):
                    continue

                connector_file_path = os.path.join(connector_path, connector_file)

                try:
                    with open(connector_file_path, "r") as f:
                        connector_data = json.load(f)

                    # Check if this is an MCP connector
                    if self._is_mcp_connector(connector_data):
                        backend_url = self._extract_backend_url(connector_data)
                        if backend_url:
                            connector_id = connector_data.get("entity_id", "unknown")
                            display_name = connector_data.get("display_name", "unknown")
                            logger.info(f"Found MCP connector: {display_name} ({connector_id})")
                            logger.info(f"  Backend URL: {COLOR_GREEN}{backend_url}{COLOR_RESET}")
                            mcp_servers.append(backend_url)
                        else:
                            logger.warning(f"MCP connector found but no backend URL: {connector_file}")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse connector file {connector_file}: {e}")
                except Exception as e:
                    logger.error(f"Error processing connector file {connector_file}: {e}")

        return mcp_servers

    def _is_mcp_connector(self, connector_data: Dict[str, Any]) -> bool:
        """
        Determine if a connector is an MCP connector based on various indicators.

        Args:
            connector_data: The connector JSON data

        Returns:
            True if the connector is an MCP connector, False otherwise
        """
        # Check various fields for MCP indicators

        # Check connector ID/name
        entity_id = connector_data.get("entity_id", "").lower()
        if "mcp" in entity_id:
            return True

        # Check display name
        display_name = connector_data.get("display_name", "").lower()
        if "mcp" in display_name:
            return True

        # Check raw_json properties
        raw_json = connector_data.get("raw_json", {})
        properties = raw_json.get("properties", {})

        # Check display name in properties
        prop_display_name = properties.get("displayName", "").lower()
        if "mcp" in prop_display_name:
            return True

        # Check swagger info
        swagger = properties.get("swagger", {})
        info = swagger.get("info", {})
        title = info.get("title", "").lower()
        description = info.get("description", "").lower()

        if "mcp" in title or "mcp" in description:
            return True

        # Check swagger paths for MCP-related tags
        paths = swagger.get("paths", {})
        for path, methods in paths.items():
            if isinstance(methods, dict):
                for method, details in methods.items():
                    if isinstance(details, dict):
                        tags = details.get("tags", [])
                        if any("mcp" in str(tag).lower() for tag in tags):
                            return True

        return False

    def _extract_backend_url(self, connector_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract the backend service URL from connector data.

        Args:
            connector_data: The connector JSON data

        Returns:
            The backend service URL or None if not found
        """
        raw_json = connector_data.get("raw_json", {})
        properties = raw_json.get("properties", {})
        backend_service = properties.get("backendService", {})
        service_url = backend_service.get("serviceUrl")

        return service_url

    async def probe_servers(self, mcp_servers: List[str]) -> List[Dict[str, Any]]:
        """
        Probe discovered MCP servers for capabilities.

        Args:
            mcp_servers: List of MCP server URLs to probe

        Returns:
            List of probe results
        """
        # Import here to avoid circular dependency and handle optional dependency
        try:
            from powerpwn.llmhound.server_probe import MCPProbe
        except ImportError as e:
            logger.error(f"Failed to import MCPProbe: {e}")
            logger.error("Probing requires aiohttp. Install with: pip install aiohttp")
            return []

        logger.info(f"\n{'=' * 70}")
        logger.info("Probe Phase - Testing MCP Server Accessibility")
        logger.info(f"{'=' * 70}")
        logger.info(f"Starting probe of {len(mcp_servers)} discovered server(s)")

        async with MCPProbe(timeout=self.__probe_timeout, max_concurrent=self.__max_concurrent_probes) as probe:
            results = await probe.probe_servers(mcp_servers)
            summary = probe.generate_summary(results)

            logger.info(f"\n{'=' * 70}")
            logger.info("Probe Summary")
            logger.info(f"{'=' * 70}")
            logger.info(f"Total servers probed: {summary['total_servers']}")
            logger.info(f"Accessible MCP endpoints: {summary['accessible_servers']}")
            logger.info(f"Inaccessible: {summary['inaccessible_servers']}")
            logger.info(f"Servers with tools: {summary['servers_with_tools']}")
            logger.info(f"Total tools found: {summary['total_tools_found']}")
            logger.info(f"Servers with resources: {summary['servers_with_resources']}")
            logger.info(f"Servers with prompts: {summary['servers_with_prompts']}")
            logger.info(f"Servers with Swagger docs: {summary['servers_with_swagger']}")

            if summary["transport_types"]:
                logger.info("\nTransport types:")
                for transport, count in summary["transport_types"].items():
                    logger.info(f"  {transport}: {count}")

            if summary.get("mcp_endpoints"):
                logger.info("\nMCP endpoint paths:")
                for endpoint, count in summary["mcp_endpoints"].items():
                    logger.info(f"  {endpoint}: {count}")

        return results

    def save_results(
        self, mcp_servers: List[str], probe_results: Optional[List[Dict[str, Any]]] = None, output_path: Optional[str] = None, urls_only: bool = False
    ) -> str:
        """
        Save the list of MCP server URLs and optional probe results to a file.

        Args:
            mcp_servers: List of MCP server URLs
            probe_results: Optional list of probe results
            output_path: Optional custom output path. If not provided, will use default location.
            urls_only: Save only URLs (simple text format) instead of full JSON

        Returns:
            The path to the output file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            if urls_only or (not probe_results):
                output_filename = f"mcp_servers_{timestamp}.txt"
            else:
                output_filename = f"mcp_recon_results_{timestamp}.json"
            output_path = os.path.join(self.__cache_path, output_filename)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        if urls_only or (not probe_results):
            # Save as simple text file (URLs only)
            with open(output_path, "w") as f:
                f.write("# MCP Server URLs\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n")
                f.write(f"# Total servers found: {len(mcp_servers)}\n\n")
                for url in mcp_servers:
                    f.write(f"{url}\n")
        else:
            # Save as JSON with both discovery and probe results
            combined_results = {
                "discovery": [{"url": url} for url in mcp_servers],
                "probe": probe_results,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_discovered": len(mcp_servers),
                    "total_probed": len(probe_results),
                    "source": "tenant_mcp_recon",
                },
            }

            with open(output_path, "w") as f:
                json.dump(combined_results, f, indent=2)

            logger.info(f"\n{'=' * 70}")
            logger.info("Results saved with discovery and probe data")
            logger.info(f"{'=' * 70}")

        logger.info(f"MCP server URLs saved to: {output_path}")
        return output_path

    def run(self, output_path: Optional[str] = None, probe: bool = True, urls_only: bool = False) -> str:
        """
        Run the MCP recon process: extract MCP servers, optionally probe them, and save results.

        Args:
            output_path: Optional custom output path
            probe: Whether to probe discovered servers (default: True)
            urls_only: Save only URLs (simple text format) instead of full JSON

        Returns:
            The path to the output file
        """
        logger.info(f"{'=' * 70}")
        logger.info("Tenant MCP Recon - Discovery and Probe")
        logger.info(f"{'=' * 70}")

        # Discovery phase
        logger.info("\n[1/2] Discovery Phase")
        logger.info(f"{'-' * 70}")
        logger.info("Scanning collected connector resources for MCP servers...")

        mcp_servers = self.extract_mcp_servers()

        if not mcp_servers:
            logger.warning("\nNo MCP servers found in the collected resources.")
            logger.info("Make sure recon has been run and MCP connectors exist in the tenant.")
            output_file = self.save_results(mcp_servers, None, output_path, urls_only)
            return output_file

        logger.info(f"\nDiscovered {len(mcp_servers)} MCP server(s)")

        # Deduplicate MCP servers
        unique_servers = list(dict.fromkeys(mcp_servers))  # Preserves order
        if len(unique_servers) < len(mcp_servers):
            logger.info(f"Removed {len(mcp_servers) - len(unique_servers)} duplicate(s), {len(unique_servers)} unique server(s) to probe")
            mcp_servers = unique_servers

        # Probe phase
        probe_results = None
        if probe:
            logger.info("\n[2/2] Probe Phase")
            logger.info(f"{'-' * 70}")
            try:
                probe_results = asyncio.run(self.probe_servers(mcp_servers))

                # Log probe success/failure summary
                if probe_results:
                    accessible_count = len([r for r in probe_results if r.get("accessible")])
                    if accessible_count == 0 and len(probe_results) > 0:
                        logger.warning(f"⚠️  All {len(probe_results)} server(s) were unreachable during probing")
                        logger.info("This could be due to: network issues, authentication requirements, or temporary server unavailability")
                        logger.info("Tip: Try running the probe command separately with 'llm-hound probe' to debug individual servers")
            except Exception as e:
                logger.error(f"Probing failed: {e}")
                logger.info("Continuing with discovery results only...")
                logger.debug(f"Full error: {e}", exc_info=True)
        else:
            logger.info("\n[2/2] Skipping probe phase (--no-probe specified)")

        # Save results
        output_file = self.save_results(mcp_servers, probe_results, output_path, urls_only)
        logger.info(f"\n{'=' * 70}")
        logger.info("MCP recon scan completed")
        logger.info(f"{'=' * 70}")

        return output_file
