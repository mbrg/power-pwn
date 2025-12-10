"""
AI Integration Surface Probing Module - Test servers for AI integration capabilities
Probes for MCP capabilities, Claude/OpenAI APIs, swagger documentation, and LLM proxies
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from powerpwn.cli.const import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None  # type: ignore

# MCP Protocol Constants
MCP_VERSION = "2024-11-05"
MCP_FALLBACK_VERSION = "2024-10-07"

# ANSI Color Codes
COLOR_GREEN = "\033[92m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"


class MCPProbe:
    """
    Probe AI integration surfaces for capabilities
    Tests for MCP protocol, Claude/OpenAI APIs, swagger documentation, and LLM proxies
    """

    def __init__(self, timeout: int = 15, max_concurrent: int = 5):
        """
        Initialize AI Integration Surface Probe

        Args:
            timeout: Connection timeout in seconds
            max_concurrent: Maximum concurrent probes
        """
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        if not AIOHTTP_AVAILABLE or aiohttp is None:
            raise ImportError("aiohttp package is required for MCP probing. Install with: pip install aiohttp")

        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout), connector=aiohttp.TCPConnector(ssl=False, limit=10))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            # Close the session
            await self.session.close()
            # Wait for underlying connections to close
            await asyncio.sleep(0.25)

    def build_mcp_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Build MCP JSON-RPC 2.0 request

        Args:
            method: MCP method name
            params: Optional parameters

        Returns:
            JSON-RPC request dict
        """
        request = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method}

        if params:
            request["params"] = params

        return request

    async def try_http_post(self, url: str, request: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Try standard HTTP POST request with optional headers"""
        if not self.session:
            return None

        try:
            async with self.session.post(url, json=request, headers=headers) as response:
                response_text = await response.text()

                # Try to parse as JSON
                try:
                    response_data = json.loads(response_text)
                    return {"status": response.status, "data": response_data, "headers": dict(response.headers)}
                except json.JSONDecodeError:
                    # Return raw text if not JSON
                    return {"status": response.status, "data": response_text, "headers": dict(response.headers)}
        except asyncio.TimeoutError:
            logger.debug(f"Timeout connecting to {url}")
        except Exception as e:
            logger.debug(f"Error connecting to {url}: {e}")

        return None

    async def try_sse_connection(self, url: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Try Server-Sent Events connection"""
        if not self.session:
            return None

        headers = {"Accept": "text/event-stream", "Cache-Control": "no-cache", "Content-Type": "application/json"}

        try:
            # Try POST with SSE headers
            async with self.session.post(url, json=request, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    parsed = self._parse_sse_content(content)
                    if parsed:
                        return parsed
        except Exception as e:
            logger.debug(f"SSE POST connection failed: {e}")

        try:
            # Try GET with SSE headers
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    parsed = self._parse_sse_content(content)
                    if parsed:
                        return parsed
        except Exception as e:
            logger.debug(f"SSE GET connection failed: {e}")

        return None

    def _parse_sse_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse Server-Sent Events content"""
        events = []

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                data_str = line[6:]  # Remove 'data: ' prefix
                try:
                    event_data = json.loads(data_str)
                    events.append(event_data)
                except json.JSONDecodeError:
                    continue

        if events:
            # Return the last/most relevant event
            return {"sse_events": events, "response": events[-1] if events else {}}

        return None

    def _is_valid_swagger_content(self, content: str, content_type: str, path: str) -> bool:
        """
        Validate that content is actually Swagger/OpenAPI documentation

        Args:
            content: Response content
            content_type: Content-Type header
            path: Endpoint path

        Returns:
            True if valid Swagger/OpenAPI content
        """
        # Check JSON endpoints (openapi.json, swagger.json, etc.)
        if "json" in path.lower() or "application/json" in content_type.lower():
            try:
                data = json.loads(content)

                # OpenAPI 3.x validation
                if "openapi" in data and isinstance(data.get("openapi"), str):
                    # Must have required OpenAPI fields
                    if "info" in data and "paths" in data:
                        logger.debug(f"    Validated OpenAPI {data['openapi']} specification")
                        return True

                # Swagger 2.0 validation
                if "swagger" in data and isinstance(data.get("swagger"), str):
                    # Must have required Swagger 2.0 fields
                    if "info" in data and "paths" in data:
                        logger.debug(f"    Validated Swagger {data['swagger']} specification")
                        return True

                return False
            except json.JSONDecodeError:
                return False

        # Check HTML endpoints (Swagger UI, ReDoc)
        elif "text/html" in content_type.lower() or path.lower() in ["/docs", "/redoc", "/swagger"]:
            content_lower = content.lower()

            # Swagger UI indicators
            swagger_ui_indicators = ["swagger-ui", "swagger ui", "swaggerui", "swagger.json", "openapi.json"]

            # ReDoc indicators
            redoc_indicators = ["redoc", "re-doc"]

            # Check for indicators
            for indicator in swagger_ui_indicators + redoc_indicators:
                if indicator in content_lower:
                    logger.debug("    Validated Swagger UI/ReDoc page")
                    return True

            return False

        return False

    async def check_swagger_endpoints(self, base_url: str) -> List[str]:
        """Check for Swagger/OpenAPI documentation endpoints and validate content

        Args:
            base_url: Base URL to check for Swagger endpoints

        Returns:
            List of full URLs (not just paths) to valid Swagger/OpenAPI documentation
        """
        if not self.session:
            return []

        swagger_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/swagger",
            "/swagger/v1/swagger.json",
            "/swagger.json",
            "/api-docs",
            "/api/swagger.json",
        ]

        found_endpoints = []

        for path in swagger_paths:
            url = urljoin(base_url, path)
            try:
                # Note: session already has timeout configured, no need for extra wrapper
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        content_type = response.headers.get("Content-Type", "")

                        # Validate that this is actually Swagger/OpenAPI content
                        if self._is_valid_swagger_content(content, content_type, path):
                            # Store full URL, not just path
                            found_endpoints.append(url)
                            logger.debug(f"  Found valid Swagger endpoint: {url}")
                        else:
                            logger.debug(f"  Skipped {url} - not valid Swagger/OpenAPI content")
            except asyncio.TimeoutError:
                logger.debug(f"  Timeout checking {url}")
                continue
            except Exception as e:
                logger.debug(f"  Error checking {url}: {e}")
                continue

        return found_endpoints

    def _is_mcp_endpoint_response(self, response_data: Any) -> bool:
        """Check if response indicates a valid MCP endpoint"""
        if not isinstance(response_data, dict):
            return False

        # Check for MCP-specific error about text/event-stream
        if "error" in response_data:
            error = response_data.get("error", {})
            if isinstance(error, dict):
                message = error.get("message", "")
                if "text/event-stream" in message.lower() or "not acceptable" in message.lower():
                    return True

        # Check for MCP success response
        if "result" in response_data and response_data.get("jsonrpc") == "2.0":
            return True

        return False

    def _ensure_dict_response(self, response: Any) -> Dict[str, Any]:
        """Ensure response is a dictionary, handling string responses"""
        if isinstance(response, dict):
            return response
        elif isinstance(response, str):
            # Try to parse string as JSON
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {}
        return {}

    def _parse_sse_response(self, data: Any) -> Any:
        """Parse SSE format response if it's a string"""
        if isinstance(data, str) and ("event:" in data or "data:" in data):
            # This looks like SSE format, try to parse it
            parsed = self._parse_sse_content(data)
            if parsed:
                return parsed
        return data

    async def probe_endpoint(self, base_url: str, endpoint_path: str = "") -> Optional[Dict[str, Any]]:
        """
        Probe a single endpoint with MCP protocol

        Args:
            base_url: Base server URL
            endpoint_path: Optional path suffix (e.g., '/mcp', '/sse')

        Returns:
            Probe result or None
        """
        url = urljoin(base_url, endpoint_path) if endpoint_path else base_url

        # First, try to detect if this is an MCP endpoint (may return "Not Acceptable" error)
        initial_request = self.build_mcp_request("tools/list", {})
        initial_response = await self.try_http_post(url, initial_request)

        if initial_response and initial_response.get("status") in [200, 406]:
            response_data = initial_response.get("data")

            # Check if this is an MCP endpoint (even if it returns an error)
            if self._is_mcp_endpoint_response(response_data):
                logger.debug(f"  Detected MCP endpoint at {url}")

                # Now try with proper MCP headers
                mcp_headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}

                # Try different MCP methods in order of priority
                methods_to_probe = [
                    ("tools/list", {}),
                    ("resources/list", {}),
                    ("prompts/list", {}),
                    (
                        "initialize",
                        {
                            "protocolVersion": MCP_VERSION,
                            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                            "clientInfo": {"name": "powerpwn-llmhound", "version": "1.0.0"},
                        },
                    ),
                ]

                for method, params in methods_to_probe:
                    request = self.build_mcp_request(method, params)

                    # Try HTTP POST with MCP headers
                    response = await self.try_http_post(url, request, headers=mcp_headers)
                    if response and response.get("status") == 200:
                        response_data = response.get("data")
                        # Parse SSE if needed
                        response_data = self._parse_sse_response(response_data)

                        return {
                            "url": url,
                            "method": method,
                            "transport": "http",
                            "success": True,
                            "response": response_data,
                            "mcp_endpoint": endpoint_path or "/",
                        }

                # If we detected MCP but couldn't get data, still return positive detection
                return {
                    "url": url,
                    "method": "detection",
                    "transport": "http",
                    "success": True,
                    "response": response_data,
                    "mcp_endpoint": endpoint_path or "/",
                    "detection_only": True,
                }

        # Try SSE as fallback
        sse_response = await self.try_sse_connection(url, initial_request)
        if sse_response:
            return {
                "url": url,
                "method": "tools/list",
                "transport": "sse",
                "success": True,
                "response": sse_response,
                "mcp_endpoint": endpoint_path or "/",
            }

        return None

    async def probe_server(self, server_url: str) -> Dict[str, Any]:
        """
        Probe an MCP server with multiple endpoint paths

        Args:
            server_url: Server URL to probe (can be base URL or include MCP endpoint path)

        Returns:
            Probe results with capabilities
        """
        # Create a short identifier for clearer async logging
        parsed = urlparse(server_url)
        server_id = f"{parsed.netloc}{parsed.path}".rstrip("/")

        result = {
            "server": server_url,
            "accessible": False,
            "transport": None,
            "mcp_endpoint": None,
            "capabilities": [],
            "tools": [],
            "resources": [],
            "prompts": [],
            "protocol_version": None,
            "swagger_endpoints": [],
            "probe_timestamp": datetime.now().isoformat(),
            "probe_details": [],
        }

        async with self.semaphore:
            try:
                logger.info(f"[{server_id}] Probing: {server_url}")
                # Add an extra timeout wrapper to ensure we never hang
                await asyncio.wait_for(
                    self._probe_server_impl(server_url, server_id, result), timeout=self.timeout + 5  # Give a bit more time than the HTTP timeout
                )
            except asyncio.TimeoutError:
                logger.info(f"[{server_id}]   {COLOR_RED}✗ Probe timed out{COLOR_RESET}")
            except Exception as e:
                logger.info(f"[{server_id}]   {COLOR_RED}✗ Probe failed: {e}{COLOR_RESET}")

            return result

    async def _probe_server_impl(self, server_url: str, server_id: str, result: Dict[str, Any]) -> None:
        """
        Internal implementation of server probing

        Args:
            server_url: Server URL to probe
            server_id: Short server identifier for logging
            result: Result dictionary to populate
        """

        # Check if URL already has a known MCP endpoint path or LLM API endpoint
        known_mcp_paths = ["/mcp", "/api/mcp", "/sse", "/message", "/mcp/sse", "/v1/chat/completions", "/v1/models", "/v1/completions"]
        url_has_mcp_path = any(server_url.rstrip("/").endswith(path) for path in known_mcp_paths)

        # Determine which paths to try
        if url_has_mcp_path:
            # URL already has MCP endpoint, try it as-is first, then try base URL with other paths
            parsed = urlparse(server_url)

            # Try the provided URL as-is first
            paths_to_try = [""]

            # Also try the base URL (without the path) with other endpoints
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            logger.debug(f"  URL contains MCP path, will also try base: {base_url}")

            # We'll handle base_url separately after trying the full URL
            try_base_url = True
        else:
            # Standard probing with all paths (MCP endpoints + OpenAI/Claude API endpoints)
            paths_to_try = [
                "/mcp",
                "/api/mcp",
                "/sse",
                "/message",
                "",
                "/mcp/sse",
                "/v1/chat/completions",
                "/v1/models",
                "/v1/completions",
            ]  # "" = Root path
            try_base_url = False

        for path in paths_to_try:
            probe_result = await self.probe_endpoint(server_url, path)

            if probe_result and probe_result.get("success"):
                result["accessible"] = True
                result["transport"] = probe_result["transport"]
                result["mcp_endpoint"] = probe_result.get("mcp_endpoint")
                result["probe_details"].append(probe_result)

                # Extract capabilities if not just detection
                if not probe_result.get("detection_only"):
                    # Ensure response is a dict before extracting capabilities
                    response_dict = self._ensure_dict_response(probe_result.get("response"))
                    capabilities = self._extract_capabilities(response_dict)
                    result["capabilities"].extend(capabilities["capabilities"])
                    result["tools"].extend(capabilities["tools"])
                    result["resources"].extend(capabilities["resources"])
                    result["prompts"].extend(capabilities["prompts"])

                    if capabilities.get("protocol_version"):
                        result["protocol_version"] = capabilities["protocol_version"]

                    # Construct full endpoint URL
                    endpoint_url = urljoin(server_url, path) if path else server_url
                    logger.info(f"[{server_id}]   ✓ MCP endpoint found at {COLOR_GREEN}{endpoint_url}{COLOR_RESET}: {probe_result['method']}")

                    # Log tools if found
                    if result["tools"]:
                        tools_display = f"{COLOR_GREEN}{', '.join(result['tools'][:5])}{COLOR_RESET}"
                        logger.info(f"[{server_id}]   ✓ Found {len(result['tools'])} tool(s): {tools_display}")
                        if len(result["tools"]) > 5:
                            logger.info(f"[{server_id}]     ... and {len(result['tools']) - 5} more")
                else:
                    endpoint_url = urljoin(server_url, path) if path else server_url
                    logger.info(f"[{server_id}]   ✓ MCP endpoint detected at {COLOR_GREEN}{endpoint_url}{COLOR_RESET} (no data retrieved)")

                # Found a working endpoint, no need to try others
                break

        # If URL had MCP path but we didn't find it, try base URL with standard paths
        if try_base_url and not result["accessible"]:
            parsed = urlparse(server_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            logger.debug(f"  Trying base URL with standard paths: {base_url}")

            for path in ["/mcp", "/api/mcp", "/sse", "/message", "/mcp/sse"]:
                probe_result = await self.probe_endpoint(base_url, path)

                if probe_result and probe_result.get("success"):
                    result["accessible"] = True
                    result["transport"] = probe_result["transport"]
                    result["mcp_endpoint"] = probe_result.get("mcp_endpoint")
                    result["probe_details"].append(probe_result)

                    # Extract capabilities if not just detection
                    if not probe_result.get("detection_only"):
                        # Ensure response is a dict before extracting capabilities
                        response_dict = self._ensure_dict_response(probe_result.get("response"))
                        capabilities = self._extract_capabilities(response_dict)
                        result["capabilities"].extend(capabilities["capabilities"])
                        result["tools"].extend(capabilities["tools"])
                        result["resources"].extend(capabilities["resources"])
                        result["prompts"].extend(capabilities["prompts"])

                        if capabilities.get("protocol_version"):
                            result["protocol_version"] = capabilities["protocol_version"]

                        endpoint_url = urljoin(base_url, path)
                        logger.info(
                            f"[{server_id}]   ✓ MCP endpoint found at base URL {COLOR_GREEN}{endpoint_url}{COLOR_RESET}: {probe_result['method']}"
                        )

                        # Log tools if found
                        if result["tools"]:
                            tools_display = f"{COLOR_GREEN}{', '.join(result['tools'][:5])}{COLOR_RESET}"
                            logger.info(f"[{server_id}]   ✓ Found {len(result['tools'])} tool(s): {tools_display}")
                            if len(result["tools"]) > 5:
                                logger.info(f"[{server_id}]     ... and {len(result['tools']) - 5} more")
                    else:
                        endpoint_url = urljoin(base_url, path)
                        logger.info(
                            f"[{server_id}]   ✓ MCP endpoint detected at base URL {COLOR_GREEN}{endpoint_url}{COLOR_RESET} (no data retrieved)"
                        )

                    # Found a working endpoint, no need to try others
                    break

        # Check for Swagger documentation (use original URL for swagger check)
        swagger_check_url = server_url.rsplit("/", 1)[0] if url_has_mcp_path else server_url
        swagger_endpoints = await self.check_swagger_endpoints(swagger_check_url)
        if swagger_endpoints:
            result["swagger_endpoints"] = swagger_endpoints
            # Display URLs in green for visibility
            logger.info(f"[{server_id}]   ✓ Found {len(swagger_endpoints)} Swagger endpoint(s):")
            for endpoint_url in swagger_endpoints:
                logger.info(f"[{server_id}]     {COLOR_GREEN}{endpoint_url}{COLOR_RESET}")

        # Remove duplicates
        result["capabilities"] = list(set(result["capabilities"]))
        result["tools"] = list(set(result["tools"]))
        result["resources"] = list(set(result["resources"]))
        result["prompts"] = list(set(result["prompts"]))

        # Always log final status
        if not result["accessible"]:
            # Check if we found Swagger endpoints even without MCP
            if result.get("swagger_endpoints"):
                logger.info(f"[{server_id}]   {COLOR_RED}✗ No MCP endpoint found (Swagger docs available){COLOR_RESET}")
            else:
                logger.info(f"[{server_id}]   {COLOR_RED}✗ No MCP endpoint found{COLOR_RESET}")
        else:
            # Log success with full endpoint URL
            if result["mcp_endpoint"]:
                full_endpoint_url = urljoin(server_url, result["mcp_endpoint"])
                logger.info(f"[{server_id}]   {COLOR_GREEN}✓ Server accessible: {full_endpoint_url}{COLOR_RESET}")
            else:
                logger.info(f"[{server_id}]   {COLOR_GREEN}✓ Server accessible: {server_url}{COLOR_RESET}")

    def _extract_capabilities(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract MCP capabilities from response"""
        caps = {"capabilities": [], "tools": [], "resources": [], "prompts": [], "protocol_version": None}

        # Ensure we have a dict to work with
        if not isinstance(response, dict):
            return caps

        # Handle SSE events
        if "sse_events" in response:
            for event in response["sse_events"]:
                if isinstance(event, dict):
                    self._parse_response_data(event, caps)
            # Also check the main response if it exists
            if "response" in response and isinstance(response["response"], dict):
                self._parse_response_data(response["response"], caps)
        elif "response" in response:
            response_data = response["response"]
            if isinstance(response_data, dict):
                self._parse_response_data(response_data, caps)
        else:
            self._parse_response_data(response, caps)

        return caps

    def _parse_response_data(self, data: Dict[str, Any], caps: Dict[str, Any]) -> None:
        """Parse response data and extract capabilities"""
        # Ensure data is a dict
        if not isinstance(data, dict):
            return

        # Look for result field (JSON-RPC response)
        result = data.get("result", data)

        # Ensure result is also a dict
        if not isinstance(result, dict):
            return

        # Protocol version
        if "protocolVersion" in result:
            caps["protocol_version"] = result["protocolVersion"]

        # Capabilities
        if "capabilities" in result:
            capability_obj = result["capabilities"]
            if isinstance(capability_obj, dict):
                for cap_type in ["tools", "resources", "prompts"]:
                    if cap_type in capability_obj:
                        caps["capabilities"].append(cap_type)

        # Tools list
        if "tools" in result and isinstance(result["tools"], list):
            for tool in result["tools"]:
                if isinstance(tool, dict) and "name" in tool:
                    caps["tools"].append(tool["name"])

        # Resources list
        if "resources" in result and isinstance(result["resources"], list):
            for resource in result["resources"]:
                if isinstance(resource, dict) and "name" in resource:
                    caps["resources"].append(resource["name"])

        # Prompts list
        if "prompts" in result and isinstance(result["prompts"], list):
            for prompt in result["prompts"]:
                if isinstance(prompt, dict) and "name" in prompt:
                    caps["prompts"].append(prompt["name"])

    async def probe_servers(self, server_urls: List[str]) -> List[Dict[str, Any]]:
        """
        Probe multiple servers concurrently

        Args:
            server_urls: List of server URLs to probe

        Returns:
            List of probe results
        """
        logger.info(f"Probing {len(server_urls)} servers...")

        tasks = [self.probe_server(url) for url in server_urls]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Fatal error during concurrent probing: {e}")
            return []

        # Filter out exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                parsed = urlparse(server_urls[i])
                server_id = f"{parsed.netloc}{parsed.path}".rstrip("/")
                logger.error(f"[{server_id}]   {COLOR_RED}✗ Error probing server: {result}{COLOR_RESET}")
            else:
                valid_results.append(result)

        logger.info(f"Probe complete: {len(valid_results)}/{len(server_urls)} servers responded")
        return valid_results

    def generate_summary(self, probe_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics from probe results"""
        total = len(probe_results)
        accessible = len([r for r in probe_results if r["accessible"]])
        with_tools = len([r for r in probe_results if r["tools"]])
        with_resources = len([r for r in probe_results if r["resources"]])
        with_prompts = len([r for r in probe_results if r["prompts"]])
        with_swagger = len([r for r in probe_results if r.get("swagger_endpoints")])

        # Transport breakdown
        transports = {}
        for result in probe_results:
            if result["accessible"] and result["transport"]:
                transport = result["transport"]
                transports[transport] = transports.get(transport, 0) + 1

        # MCP endpoint breakdown
        mcp_endpoints = {}
        for result in probe_results:
            if result["accessible"] and result.get("mcp_endpoint"):
                endpoint = result["mcp_endpoint"]
                mcp_endpoints[endpoint] = mcp_endpoints.get(endpoint, 0) + 1

        # Total tools found
        total_tools = sum(len(r["tools"]) for r in probe_results)

        return {
            "total_servers": total,
            "accessible_servers": accessible,
            "inaccessible_servers": total - accessible,
            "servers_with_tools": with_tools,
            "servers_with_resources": with_resources,
            "servers_with_prompts": with_prompts,
            "servers_with_swagger": with_swagger,
            "total_tools_found": total_tools,
            "transport_types": transports,
            "mcp_endpoints": mcp_endpoints,
        }


async def probe_single_url(url: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Convenience function to probe a single URL

    Args:
        url: Server URL to probe
        timeout: Connection timeout in seconds

    Returns:
        Probe result with capabilities

    Example:
        >>> import asyncio
        >>> result = asyncio.run(probe_single_url("http://localhost:8000"))
        >>> print(f"Accessible: {result['accessible']}")
        >>> print(f"Tools: {result['tools']}")
    """
    async with MCPProbe(timeout=timeout, max_concurrent=1) as probe:
        return await probe.probe_server(url)
