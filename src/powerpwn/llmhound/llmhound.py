"""
LLM Hound - Main module for discovering and probing AI integration surfaces
Discovers Claude/OpenAI APIs, Model Context Protocol (MCP) servers, LLM proxies, and API endpoints
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.llmhound.registry_discovery import MCPRegistryDiscovery
from powerpwn.llmhound.server_probe import MCPProbe
from powerpwn.llmhound.shodan_discovery import MCPDiscovery

logger = logging.getLogger(LOGGER_NAME)

# ANSI Color Codes
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"


class LLMHound:
    """
    Main class orchestrating AI integration surface discovery and probing
    Discovers Claude/OpenAI APIs, MCP servers, LLM proxies, and API endpoints
    """

    def __init__(
        self, shodan_api_key: Optional[str] = None, filters_file: Optional[str] = None, probe_timeout: int = 15, max_concurrent_probes: int = 5
    ):
        """
        Initialize LLM Hound

        Args:
            shodan_api_key: Shodan API key (required for discovery)
            filters_file: Path to custom filters JSON
            probe_timeout: Timeout for probing servers
            max_concurrent_probes: Max concurrent probe connections
        """
        self.shodan_api_key = shodan_api_key
        self.filters_file = filters_file
        self.probe_timeout = probe_timeout
        self.max_concurrent_probes = max_concurrent_probes

        # Initialize discovery if API key provided
        self.discovery = None
        if shodan_api_key:
            self.discovery = MCPDiscovery(api_key=shodan_api_key, filters_file=filters_file)

    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate discovery results based on URL

        Args:
            results: List of discovery results

        Returns:
            Deduplicated list of results (preserves order, first occurrence wins)
        """
        seen_urls = set()
        unique_results = []

        for result in results:
            url = result.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        duplicates_removed = len(results) - len(unique_results)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate server(s) from results")

        return unique_results

    def list_filters(self) -> None:
        """List all available discovery filters"""
        if not self.discovery:
            logger.error("Discovery not initialized. Shodan API key required.")
            return

        filters = self.discovery.list_available_filters()

        logger.info("=" * 70)
        logger.info("Available LLM Hound Discovery Filters")
        logger.info("=" * 70)

        # Group by category
        by_category: Dict[str, List[Dict[str, Any]]] = {}
        for f in filters:
            category = f["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(f)

        for category, category_filters in by_category.items():
            logger.info(f"\n{category.upper().replace('_', ' ')}")
            logger.info("-" * 70)

            for f in category_filters:
                logger.info(f"  {f['name']}")
                logger.info(f"    Description: {f['description']}")
                logger.info(f"    Tags: {', '.join(f['tags'])}")
                logger.info(f"    Query: {f['query']}")
                logger.info("")

    def discover_servers(
        self, filter_name: Optional[str] = None, category: Optional[str] = None, custom_query: Optional[str] = None, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Discover AI integration surfaces using Shodan (Claude/OpenAI APIs, MCP servers, LLM proxies)

        Args:
            filter_name: Specific filter to use
            category: Category of filters to use
            custom_query: Custom Shodan query
            max_results: Maximum results

        Returns:
            List of discovered servers
        """
        if not self.discovery:
            logger.error("Discovery not initialized. Shodan API key required.")
            return []

        results = []

        if custom_query:
            logger.info("Using custom Shodan query")
            results = self.discovery.search_with_custom_query(custom_query, max_results=max_results)
        elif filter_name:
            logger.info(f"Using filter: {filter_name}")
            results = self.discovery.search_with_filter(filter_name, max_results=max_results)
        elif category:
            logger.info(f"Using category: {category}")
            category_results = self.discovery.search_by_category(category, max_results_per_filter=max_results)
            # Flatten results
            for filter_results in category_results.values():
                results.extend(filter_results)
            # Deduplicate based on URL
            results = self._deduplicate_results(results)
        else:
            logger.error("Must specify filter_name, category, or custom_query")
            return []

        return results

    async def probe_servers(self, server_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Probe servers for AI integration capabilities (MCP, Claude/OpenAI APIs, swagger endpoints)

        Args:
            server_urls: List of server URLs to probe

        Returns:
            List of probe results
        """
        logger.info(f"Starting probe of {len(server_urls)} servers")

        async with MCPProbe(timeout=self.probe_timeout, max_concurrent=self.max_concurrent_probes) as probe:
            results = await probe.probe_servers(server_urls)
            summary = probe.generate_summary(results)

            logger.info("\n" + "=" * 70)
            logger.info("Probe Summary")
            logger.info("=" * 70)
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

    def load_server_list(self, file_path: str) -> List[str]:
        """Load server URLs from file (one per line)"""
        try:
            with open(file_path, "r") as f:
                servers = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            # Deduplicate URLs while preserving order
            unique_servers = list(dict.fromkeys(servers))

            logger.info(f"Loaded {len(servers)} servers from {file_path}")
            if len(unique_servers) < len(servers):
                logger.info(f"Removed {len(servers) - len(unique_servers)} duplicate(s), {len(unique_servers)} unique server(s)")

            return unique_servers
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return []

    def print_detailed_result(self, result: Dict[str, Any]) -> None:
        """
        Print detailed results for a single server probe

        Args:
            result: Probe result dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info(f"MCP Server: {COLOR_GREEN if result['accessible'] else COLOR_RED}{result['server']}{COLOR_RESET}")
        logger.info("=" * 70)

        if result["accessible"]:
            logger.info(f"Status: {COLOR_GREEN}✓ ACCESSIBLE{COLOR_RESET}")
            logger.info(f"MCP Endpoint: {COLOR_GREEN}{result.get('mcp_endpoint', 'N/A')}{COLOR_RESET}")
            logger.info(f"Transport: {result.get('transport', 'N/A')}")

            if result.get("protocol_version"):
                logger.info(f"Protocol Version: {result['protocol_version']}")

            if result["tools"]:
                logger.info(f"\nTools ({len(result['tools'])}):")
                for tool in result["tools"]:
                    logger.info(f"  • {COLOR_GREEN}{tool}{COLOR_RESET}")

            if result["resources"]:
                logger.info(f"\nResources ({len(result['resources'])}):")
                for resource in result["resources"]:
                    logger.info(f"  • {COLOR_GREEN}{resource}{COLOR_RESET}")

            if result["prompts"]:
                logger.info(f"\nPrompts ({len(result['prompts'])}):")
                for prompt in result["prompts"]:
                    logger.info(f"  • {COLOR_GREEN}{prompt}{COLOR_RESET}")

            if result.get("swagger_endpoints"):
                logger.info("\nSwagger Documentation:")
                for endpoint_url in result["swagger_endpoints"]:
                    logger.info(f"  • {COLOR_GREEN}{endpoint_url}{COLOR_RESET}")
        else:
            logger.info(f"Status: {COLOR_RED}✗ NOT ACCESSIBLE{COLOR_RESET}")

        logger.info("=" * 70)

    def save_results(self, results: Any, output_file: str, format: str = "json") -> None:
        """
        Save results to file

        Args:
            results: Results to save
            output_file: Output file path
            format: Output format ('json' or 'txt')
        """
        try:
            if format == "json":
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)
            elif format == "txt":
                with open(output_file, "w") as f:
                    if isinstance(results, list):
                        for item in results:
                            if isinstance(item, dict) and "url" in item:
                                f.write(f"{item['url']}\n")
                            elif isinstance(item, str):
                                f.write(f"{item}\n")

            logger.info(f"Results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    async def run_discovery_and_probe(
        self,
        filter_name: Optional[str] = None,
        category: Optional[str] = None,
        custom_query: Optional[str] = None,
        max_results: int = 100,
        output_file: Optional[str] = None,
        probe: bool = True,
        urls_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Run full workflow: discover and probe AI integration surfaces

        Args:
            filter_name: Filter to use
            category: Category to use
            custom_query: Custom query
            max_results: Max discovery results
            output_file: Output file path
            probe: Whether to probe discovered servers
            urls_only: Save only URLs (simple text format) instead of full JSON

        Returns:
            Combined results
        """
        logger.info("=" * 70)
        logger.info("LLM Hound - Discovery and Probe")
        logger.info("=" * 70)

        # Discovery phase
        logger.info("\n[1/2] Discovery Phase")
        logger.info("-" * 70)

        discovery_results = self.discover_servers(filter_name=filter_name, category=category, custom_query=custom_query, max_results=max_results)

        if not discovery_results:
            logger.warning("No servers discovered")
            return {"discovery": [], "probe": []}

        # Extract server URLs
        server_urls = self.discovery.extract_server_list(discovery_results) if self.discovery else []

        logger.info(f"Discovered {len(server_urls)} unique servers")

        # Probe phase
        probe_results = []
        if probe and server_urls:
            logger.info("\n[2/2] Probe Phase")
            logger.info("-" * 70)

            probe_results = await self.probe_servers(server_urls)
        elif not probe:
            logger.info("\nSkipping probe phase (--no-probe specified)")

        # Save results
        if output_file:
            if urls_only:
                # Save simple URL list
                with open(output_file, "w") as f:
                    for url in server_urls:
                        f.write(f"{url}\n")
                logger.info(f"Server URLs saved to: {output_file}")
            else:
                # Save full JSON with all details
                combined_results = {
                    "discovery": discovery_results,
                    "probe": probe_results,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "total_discovered": len(discovery_results),
                        "total_probed": len(probe_results),
                        "filter_used": filter_name or category or "custom",
                    },
                }
                self.save_results(combined_results, output_file, format="json")

        # Always return combined results for internal use
        combined_results = {
            "discovery": discovery_results,
            "probe": probe_results,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_discovered": len(discovery_results),
                "total_probed": len(probe_results),
                "filter_used": filter_name or category or "custom",
            },
        }

        return combined_results

    async def run_probe_only(self, server_list_file: str, output_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Probe servers from a file (discovery already done)

        Args:
            server_list_file: File containing server URLs
            output_file: Output file for results

        Returns:
            Probe results
        """
        logger.info("=" * 70)
        logger.info("LLM Hound - Probe Mode")
        logger.info("=" * 70)

        servers = self.load_server_list(server_list_file)

        if not servers:
            logger.error("No servers to probe")
            return []

        probe_results = await self.probe_servers(servers)

        if output_file:
            self.save_results(probe_results, output_file, format="json")

        return probe_results

    async def run_probe_single_url(self, server_url: str, output_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Probe a single server URL

        Args:
            server_url: Server URL to probe
            output_file: Output file for results

        Returns:
            Probe results (as single-item list for consistency)
        """
        logger.info("=" * 70)
        logger.info("LLM Hound - Single URL Probe Mode")
        logger.info("=" * 70)
        logger.info(f"Target: {server_url}\n")

        probe_results = await self.probe_servers([server_url])

        # Display detailed results for single URL
        if probe_results:
            self.print_detailed_result(probe_results[0])

        if output_file:
            self.save_results(probe_results, output_file, format="json")

        return probe_results

    async def run_registry_diving(
        self, max_results: Optional[int] = None, output_file: Optional[str] = None, probe: bool = True, urls_only: bool = False
    ) -> Dict[str, Any]:
        """
        Discover MCP servers from official registry and optionally probe them

        Args:
            max_results: Maximum number of results
            output_file: Output file path
            probe: Whether to probe discovered servers
            urls_only: Save only URLs (simple text format) instead of full JSON

        Returns:
            Combined results
        """
        logger.info("=" * 70)
        logger.info("LLM Hound - Registry Diving")
        logger.info("=" * 70)

        # Discovery phase
        logger.info("\n[1/2] Registry Discovery Phase")
        logger.info("-" * 70)

        try:
            registry = MCPRegistryDiscovery()  # type: ignore[no-untyped-call]
            discovery_results = registry.discover_servers(max_results=max_results)
        except ImportError as e:
            logger.error(f"Registry discovery failed: {e}")
            return {"discovery": [], "probe": []}

        if not discovery_results:
            logger.warning("No servers with remote endpoints found in registry")
            return {"discovery": [], "probe": []}

        # Extract server URLs
        server_urls = registry.extract_server_list(discovery_results)
        logger.info(f"\nDiscovered {len(server_urls)} unique server endpoints")

        # Probe phase
        probe_results = []
        if probe and server_urls:
            logger.info("\n[2/2] Probe Phase")
            logger.info("-" * 70)

            probe_results = await self.probe_servers(server_urls)
        elif not probe:
            logger.info("\nSkipping probe phase (--no-probe specified)")

        # Save results
        if output_file:
            if urls_only:
                # Save simple URL list
                with open(output_file, "w") as f:
                    for url in server_urls:
                        f.write(f"{url}\n")
                logger.info(f"Server URLs saved to: {output_file}")
            else:
                # Save full JSON with all details
                combined_results = {
                    "discovery": discovery_results,
                    "probe": probe_results,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "total_discovered": len(discovery_results),
                        "total_probed": len(probe_results),
                        "source": "mcp_registry",
                    },
                }
                self.save_results(combined_results, output_file, format="json")

        # Always return combined results for internal use
        combined_results = {
            "discovery": discovery_results,
            "probe": probe_results,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_discovered": len(discovery_results),
                "total_probed": len(probe_results),
                "source": "mcp_registry",
            },
        }

        return combined_results
