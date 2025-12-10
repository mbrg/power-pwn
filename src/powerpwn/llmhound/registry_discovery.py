"""
MCP Registry Discovery - Query official MCP registry for registered servers
Part of LLM Hound's discovery capabilities
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from powerpwn.cli.const import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None  # type: ignore[assignment]


class MCPRegistryDiscovery:
    """
    Discovers MCP servers from the official MCP registry
    Part of LLM Hound's discovery capabilities for AI integration surfaces
    """

    REGISTRY_API_URL = "https://registry.modelcontextprotocol.io/v0.1/servers"

    def __init__(self) -> None:
        """Initialize MCP Registry Discovery"""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests package is required for registry discovery. Install with: pip install requests")

        if requests is None:
            raise ImportError("requests module not available")

    def fetch_and_filter_servers(self, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch servers from MCP registry with pagination, filtering for remote endpoints as we go

        Args:
            max_results: Maximum number of remote endpoints to find

        Returns:
            List of discovered MCP servers with remote endpoints
        """
        remote_servers = []
        seen_urls = set()  # Track unique URLs for deduplication
        cursor: Optional[str] = None
        page = 1
        total_processed = 0

        try:
            logger.info(f"Fetching servers from MCP registry: {self.REGISTRY_API_URL}")

            while True:
                # Build URL with cursor if we have one
                params: Dict[str, str] = {}
                if cursor:
                    params["cursor"] = cursor

                response = requests.get(self.REGISTRY_API_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                servers = data.get("servers", [])
                metadata = data.get("metadata", {})

                if not servers:
                    break

                # Process this page's servers
                for entry in servers:
                    total_processed += 1
                    server_data = entry.get("server", {})

                    name = server_data.get("name", "unknown")
                    description = server_data.get("description", "")
                    version = server_data.get("version", "")

                    # Method 1: Check for "remotes" field (some servers use this)
                    remotes = server_data.get("remotes", [])
                    for remote in remotes:
                        remote_type = remote.get("type", "unknown")
                        url = remote.get("url", "")

                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            parsed = urlparse(url)

                            server_info = {
                                "name": name,
                                "description": description,
                                "version": version,
                                "url": url,
                                "hostname": parsed.hostname or "",
                                "port": parsed.port or (443 if parsed.scheme == "https" else 80),
                                "protocol": parsed.scheme or "https",
                                "transport_type": remote_type,
                                "source": "mcp_registry",
                                "discovered_at": datetime.now().isoformat(),
                            }

                            remote_servers.append(server_info)
                            logger.info(f"  {GREEN}✓ Found:{RESET} {name} - {url} ({GREEN}{len(remote_servers)}/{max_results or '∞'}{RESET})")

                            if max_results and len(remote_servers) >= max_results:
                                logger.info(f"\n{GREEN}✓ Target reached: {max_results} unique remote endpoints found!{RESET}")
                                logger.info(f"{YELLOW}Processed {total_processed} servers across {page} page(s){RESET}")
                                return remote_servers

                    # Method 2: Check for "packages" with remote transports
                    packages = server_data.get("packages", [])
                    for package in packages:
                        transport = package.get("transport", {})
                        transport_type = transport.get("type", "").lower()

                        # Check if this is a remote transport (HTTP/HTTPS/SSE)
                        if transport_type in ["http", "https", "sse"]:
                            # Try multiple locations for URL
                            url = transport.get("url") or transport.get("endpoint") or package.get("url", "") or package.get("endpoint", "")

                            # Skip if no URL or duplicate
                            if not url or url in seen_urls:
                                continue

                            seen_urls.add(url)
                            parsed = urlparse(url)

                            server_info = {
                                "name": name,
                                "description": description,
                                "version": version,
                                "url": url,
                                "hostname": parsed.hostname or "",
                                "port": parsed.port or (443 if parsed.scheme == "https" else 80),
                                "protocol": parsed.scheme or "https",
                                "transport_type": transport_type,
                                "source": "mcp_registry",
                                "discovered_at": datetime.now().isoformat(),
                            }

                            remote_servers.append(server_info)
                            logger.info(f"  {GREEN}✓ Found:{RESET} {name} - {url} ({GREEN}{len(remote_servers)}/{max_results or '∞'}{RESET})")

                            # Check if we've reached our target
                            if max_results and len(remote_servers) >= max_results:
                                logger.info(f"\n{GREEN}✓ Target reached: {max_results} unique remote endpoints found!{RESET}")
                                logger.info(f"{YELLOW}Processed {total_processed} servers across {page} page(s){RESET}")
                                return remote_servers

                logger.info(f"  Page {page}: Scanned 30 servers ({total_processed} total)")

                # Check for next page
                next_cursor = metadata.get("nextCursor")
                if not next_cursor:
                    break

                cursor = next_cursor
                page += 1

            logger.info(f"\n{GREEN}✓ Scan complete: Found {len(remote_servers)} unique remote endpoints{RESET}")
            logger.info(f"{YELLOW}Processed {total_processed} servers across {page} page(s){RESET}")
            return remote_servers

        except requests.RequestException as e:
            logger.error(f"Failed to fetch from registry: {e}")
            return remote_servers
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse registry response: {e}")
            return remote_servers

    def discover_servers(self, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Full discovery workflow: fetch and process registry servers

        Args:
            max_results: Maximum number of results to return

        Returns:
            List of discovered MCP servers with remote endpoints
        """
        logger.info("=" * 70)
        logger.info("MCP Registry Discovery")
        logger.info("=" * 70)

        # Fetch and filter in one pass (stops early when target is reached)
        remote_servers = self.fetch_and_filter_servers(max_results)

        if not remote_servers:
            logger.warning(f"\n{YELLOW}No remote servers found in registry{RESET}")
            return []

        logger.info(f"\n{GREEN}={'='*70}{RESET}")
        logger.info(f"{GREEN}DISCOVERY SUMMARY{RESET}")
        logger.info(f"{GREEN}={'='*70}{RESET}")
        logger.info(f"{GREEN}Found {len(remote_servers)} unique remote endpoint(s){RESET}")

        if remote_servers:
            logger.info(f"\n{GREEN}Discovered servers:{RESET}")
            for server in remote_servers:
                logger.info(f"  {GREEN}✓{RESET} {server['name']}: {server['url']}")

        return remote_servers

    def extract_server_list(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract list of server URLs from results

        Args:
            results: Discovery results

        Returns:
            List of server URLs
        """
        servers = [r["url"] for r in results if "url" in r]

        # Remove duplicates while preserving order
        seen = set()
        unique_servers = []
        for server in servers:
            if server not in seen:
                seen.add(server)
                unique_servers.append(server)

        return unique_servers

    def save_results(self, results: List[Dict[str, Any]], output_file: str) -> None:
        """
        Save discovery results to JSON file

        Args:
            results: Results to save
            output_file: Output file path
        """
        try:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
