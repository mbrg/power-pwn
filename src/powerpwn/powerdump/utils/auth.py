import logging
from typing import Optional

import msal

from powerpwn.cli.const import LOGGER_NAME, TOOL_NAME
from powerpwn.powerdump.utils.const import API_HUB_SCOPE, AZURE_CLI_APP_ID, GRAPH_API_SCOPE, POWER_APPS_SCOPE
from powerpwn.powerdump.utils.token_cache import TOKEN_CACHE_PATH, TokenCache, put_token, put_tokens, try_fetch_token

logger = logging.getLogger(LOGGER_NAME)

AZURE_CLI_REFRESH_TOKEN = "cli_refresh_token"  # nosec
POWERAPPS_ACCESS_TOKEN = "powerapps_access_token"  # nosec
APIHUB_ACCESS_TOKEN = "apihub_access_token"  # nosec

SCOPE_TO_TOKEN_CACHE_TYPE = {API_HUB_SCOPE: APIHUB_ACCESS_TOKEN, POWER_APPS_SCOPE: POWERAPPS_ACCESS_TOKEN}


def acquire_token(scope: str, tenant: Optional[str] = None) -> str:
    """
    Leverage family refresh tokens to acquire a Graph API refresh token and exchange it for other required scopes
    https://github.com/secureworks/family-of-client-ids-research
    :param scope: token scope
    :return: Bearer token
    """
    logger.info(f"Acquiring token with scope={scope}.")

    azure_cli_client = __get_msal_cli_application(tenant)

    # Acquire Graph API refresh token
    device_flow = azure_cli_client.initiate_device_flow(scopes=[GRAPH_API_SCOPE])
    print(device_flow["message"])
    azure_cli_bearer_tokens_for_graph_api = azure_cli_client.acquire_token_by_device_flow(device_flow)  # blocking

    azure_cli_app_refresh_token = azure_cli_bearer_tokens_for_graph_api.get("refresh_token")

    azure_cli_bearer_tokens_for_scope = (
        # Same client as original authorization
        azure_cli_client.acquire_token_by_refresh_token(
            azure_cli_app_refresh_token,
            # But different scopes than original authorization
            scopes=[scope],
        )
    )

    bearer = azure_cli_bearer_tokens_for_scope.get("token_type") + " " + azure_cli_bearer_tokens_for_scope.get("access_token")
    logger.info(f"Access token for {scope} acquired successfully")

    # cache refresh token for cli to use in further FOCI authentication
    # cache access token for required scope
    tokens_to_cache = [
        TokenCache(token_key=AZURE_CLI_REFRESH_TOKEN, token_val=azure_cli_app_refresh_token),
        TokenCache(SCOPE_TO_TOKEN_CACHE_TYPE[scope], bearer),
    ]
    put_tokens(tokens_to_cache)
    logger.info(f"Token is cached in {TOKEN_CACHE_PATH}")

    return bearer


def acquire_token_from_cached_refresh_token(scope: str, tenant: Optional[str] = None) -> str:
    """
    Leverage family refresh tokens to acquire a Graph API refresh token and exchange it for other required scopes
    https://github.com/secureworks/family-of-client-ids-research
    :param scope: token scope
    :return: Bearer token
    """
    logger.info(f"Acquiring token with scope={scope} from cached refresh token.")

    cached_refresh_token = try_fetch_token(AZURE_CLI_REFRESH_TOKEN)

    if not cached_refresh_token:
        logger.info("Failed to acquire with refresh token. Fallback to device-flow")
        return acquire_token(scope, tenant)

    azure_cli_client = __get_msal_cli_application(tenant)

    azure_cli_bearer_tokens_for_scope = (
        # Same client as original authorization
        azure_cli_client.acquire_token_by_refresh_token(
            cached_refresh_token,
            # But different scopes than original authorization
            scopes=[scope],
        )
    )

    bearer = azure_cli_bearer_tokens_for_scope.get("token_type") + " " + azure_cli_bearer_tokens_for_scope.get("access_token")
    logger.info(f"Token for {scope} acquired from refresh token successfully.")

    # cache access token for required scope
    tokens_to_cache = TokenCache(SCOPE_TO_TOKEN_CACHE_TYPE[scope], bearer)
    put_token(tokens_to_cache)
    logger.info(f"Token is cached in {TOKEN_CACHE_PATH}")

    return bearer


def __get_msal_cli_application(tenant: Optional[str] = None) -> msal.PublicClientApplication:
    if tenant:
        authority = authority = f"https://login.microsoftonline.com/{tenant}"
        return msal.PublicClientApplication(AZURE_CLI_APP_ID, authority=authority, app_name=TOOL_NAME)
    else:
        return msal.PublicClientApplication(AZURE_CLI_APP_ID, app_name=TOOL_NAME)
