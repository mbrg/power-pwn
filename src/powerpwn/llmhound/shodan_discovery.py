"""
Shodan-based AI integration surface discovery module
Discovers Claude/OpenAI APIs, MCP servers, LLM proxies, and API endpoints
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from powerpwn.cli.const import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

try:
    import shodan

    SHODAN_AVAILABLE = True
except ImportError:
    SHODAN_AVAILABLE = False
    shodan = None  # type: ignore[assignment]


class MCPDiscovery:
    """
    Discovers AI integration surfaces using Shodan search with modular filters
    Finds Claude/OpenAI APIs, MCP servers, LLM proxies, and API endpoints
    """

    def __init__(self, api_key: str, filters_file: Optional[str] = None):
        """
        Initialize MCP Discovery

        Args:
            api_key: Shodan API key
            filters_file: Path to custom filters JSON file
        """
        if not SHODAN_AVAILABLE:
            raise ImportError("shodan package is required for MCP discovery. Install with: pip install shodan")

        if shodan is None:
            raise ImportError("shodan module not available")

        self.api = shodan.Shodan(api_key)
        self.filters = self._load_filters(filters_file)

    def _load_filters(self, filters_file: Optional[str] = None) -> Dict[str, Any]:
        """Load filters from JSON file"""
        if filters_file is None:
            # Use default bundled filters
            current_dir = Path(__file__).parent
            filters_file = str(current_dir / "discovery_filters.json")

        try:
            with open(filters_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Filters file not found: {filters_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in filters file: {e}")
            raise

    def list_available_filters(self) -> List[Dict[str, Any]]:
        """Get list of all available filters"""
        all_filters = []

        for category_name, category_data in self.filters.get("filter_categories", {}).items():
            for filter_def in category_data.get("filters", []):
                all_filters.append(
                    {
                        "category": category_name,
                        "name": filter_def["name"],
                        "description": filter_def["description"],
                        "tags": filter_def.get("tags", []),
                        "query": filter_def["query"],
                    }
                )

        return all_filters

    def get_filter_by_name(self, filter_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific filter by name"""
        for category_data in self.filters.get("filter_categories", {}).values():
            for filter_def in category_data.get("filters", []):
                if filter_def["name"] == filter_name:
                    return filter_def
        return None

    def search_with_filter(self, filter_name: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search Shodan using a specific filter with automatic pagination

        Args:
            filter_name: Name of the filter to use
            max_results: Maximum number of results to return

        Returns:
            List of discovered servers with metadata
        """
        filter_def = self.get_filter_by_name(filter_name)

        if not filter_def:
            logger.error(f"Filter not found: {filter_name}")
            return []

        query = filter_def["query"]
        logger.info(f"Using filter: {filter_name}")
        logger.info(f"Query: {query}")

        servers: List[Dict[str, Any]] = []

        try:
            # Use search_cursor for automatic pagination
            logger.info(f"Fetching up to {max_results} results...")

            for result in self.api.search_cursor(query):
                if len(servers) >= max_results:
                    break

                server_info = self._extract_server_info(result, filter_def)
                servers.append(server_info)

                # Log progress periodically
                if len(servers) % 10 == 0:
                    logger.info(f"  Retrieved {len(servers)} results so far...")

            logger.info(f"Found {len(servers)} servers using filter '{filter_name}'")
            return servers

        except shodan.APIError as e:
            if "upgrade your API plan" in str(e).lower():
                logger.warning(f"API plan limit reached. Retrieved {len(servers)} results.")
                return servers
            logger.error(f"Shodan API error: {e}")
            return []

    def search_with_custom_query(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search Shodan with a custom query with automatic pagination

        Args:
            query: Custom Shodan search query
            max_results: Maximum number of results

        Returns:
            List of discovered servers
        """
        logger.info(f"Custom query: {query}")

        servers: List[Dict[str, Any]] = []

        try:
            # Use search_cursor for automatic pagination
            logger.info(f"Fetching up to {max_results} results...")

            for result in self.api.search_cursor(query):
                if len(servers) >= max_results:
                    break

                server_info = self._extract_server_info(result, {"name": "custom", "tags": ["custom"]})
                servers.append(server_info)

                # Log progress periodically
                if len(servers) % 10 == 0:
                    logger.info(f"  Retrieved {len(servers)} results so far...")

            logger.info(f"Found {len(servers)} servers")
            return servers

        except shodan.APIError as e:
            if "upgrade your API plan" in str(e).lower():
                logger.warning(f"API plan limit reached. Retrieved {len(servers)} results.")
                return servers
            logger.error(f"Shodan API error: {e}")
            return []

    def search_multiple_filters(self, filter_names: List[str], max_results_per_filter: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search using multiple filters

        Args:
            filter_names: List of filter names to use
            max_results_per_filter: Max results per filter

        Returns:
            Dictionary mapping filter names to their results
        """
        all_results = {}

        for filter_name in filter_names:
            logger.info(f"\nSearching with filter: {filter_name}")
            results = self.search_with_filter(filter_name, max_results=max_results_per_filter)
            all_results[filter_name] = results

        return all_results

    def search_by_category(self, category: str, max_results_per_filter: int = 50) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search using all filters in a specific category

        Args:
            category: Category name (e.g., 'protocol_based', 'infrastructure_based')
            max_results_per_filter: Max results per filter

        Returns:
            Dictionary of results by filter name
        """
        if category not in self.filters.get("filter_categories", {}):
            logger.error(f"Category not found: {category}")
            return {}

        category_data = self.filters["filter_categories"][category]
        filter_names = [f["name"] for f in category_data.get("filters", [])]

        logger.info(f"Searching category '{category}' with {len(filter_names)} filters")
        return self.search_multiple_filters(filter_names, max_results_per_filter)

    def _extract_server_info(self, shodan_result: Dict[str, Any], filter_def: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant information from Shodan result"""
        hostnames = shodan_result.get("hostnames", [])
        return {
            "ip": shodan_result.get("ip_str", ""),
            "port": shodan_result.get("port", 0),
            "hostname": hostnames[0] if hostnames else None,
            "url": self._construct_url(shodan_result),
            "organization": shodan_result.get("org", ""),
            "isp": shodan_result.get("isp", ""),
            "country": shodan_result.get("location", {}).get("country_name", ""),
            "city": shodan_result.get("location", {}).get("city", ""),
            "product": shodan_result.get("product", ""),
            "version": shodan_result.get("version", ""),
            "ssl": shodan_result.get("ssl", {}) != {},
            "filter_used": filter_def["name"],
            "filter_tags": filter_def.get("tags", []),
            "discovered_at": datetime.now().isoformat(),
            "raw_data": shodan_result.get("data", ""),
        }

    def _construct_url(self, result: Dict[str, Any]) -> str:
        """Construct full URL from Shodan result"""
        ip = result.get("ip_str", "")
        port = result.get("port", 80)
        hostnames = result.get("hostnames", [])

        # Prefer hostname over IP
        host = hostnames[0] if hostnames else ip

        # Determine protocol
        protocol = "https" if result.get("ssl") or port == 443 else "http"

        # Construct URL
        if (protocol == "https" and port == 443) or (protocol == "http" and port == 80):
            return f"{protocol}://{host}"
        else:
            return f"{protocol}://{host}:{port}"

    def save_results(self, results: Any, output_file: str) -> None:
        """
        Save discovery results to JSON file

        Args:
            results: Results to save (list or dict)
            output_file: Output file path
        """
        try:
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    def extract_server_list(self, results: Any) -> List[str]:
        """
        Extract list of server URLs from results

        Args:
            results: Discovery results (list or dict)

        Returns:
            List of server URLs
        """
        servers = []

        if isinstance(results, list):
            servers = [r["url"] for r in results if "url" in r]
        elif isinstance(results, dict):
            for filter_results in results.values():
                servers.extend([r["url"] for r in filter_results if "url" in r])

        # Remove duplicates while preserving order
        seen = set()
        unique_servers = []
        for server in servers:
            if server not in seen:
                seen.add(server)
                unique_servers.append(server)

        return unique_servers
