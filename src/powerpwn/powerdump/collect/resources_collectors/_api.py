from typing import Any, Dict, Generator, List, Optional

import requests


def list_connectors(session: requests.Session, environment_id: str) -> Generator[Dict[str, Any], None, None]:
    yield from __paginate(
        session,
        "https://api.powerapps.com/providers/Microsoft.PowerApps/apis",
        {"api-version": "2016-11-01", "$filter": f"environment eq '{environment_id}'"},
        f"get_connectors(environment_id={environment_id})",
    )


def get_connector(session: requests.Session, environment_id: str, connector_id: str):
    resp = session.get(
        url=f"https://api.powerapps.com/providers/Microsoft.PowerApps/apis/{connector_id}",
        params={"api-version": "2016-11-01", "$filter": f"environment eq '{environment_id}'"},
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Got status code {resp.status_code} for get_connector(environment_id={environment_id}, connector_name={connector_id}): {str(resp.content)}."
        )
    return resp.json()


def list_connections(session: requests.Session, environment_id: str) -> Generator[Dict[str, Any], None, None]:
    yield from __paginate(
        session,
        "https://api.powerapps.com/providers/Microsoft.PowerApps/connections",
        {"api-version": "2016-11-01", "$filter": f"environment eq '{environment_id}'"},
        f"list_connections(environment_id={environment_id})",
    )


def list_canvas_apps(session: requests.Session, environment_id: str) -> Generator[Dict[str, Any], None, None]:
    yield from __paginate(
        session,
        "https://api.powerapps.com/providers/Microsoft.PowerApps/apps",
        {"api-version": "2016-11-01", "$filter": f"environment eq '{environment_id}'"},
        f"list_canvas_apps(environment_id={environment_id})",
    )


def list_canvas_app_rbac(session: requests.Session, app_id: str, environment_id: str) -> Generator[Dict[str, Any], None, None]:
    yield from __paginate(
        session,
        f"https://api.powerapps.com/providers/Microsoft.PowerApps/apps/{app_id}/permissions",
        {"api-version": "2016-11-01", "$filter": f"environment eq '{environment_id}'"},
        f"list_canvas_app_rbac(environment_id={environment_id})",
    )


def list_environments(session: requests.Session) -> List[str]:
    resp = session.get(url="https://api.powerapps.com/providers/Microsoft.PowerApps/environments", params={"api-version": "2016-11-01"})
    if resp.status_code != 200:
        raise RuntimeError(f"Got status code {resp.status_code} for list_environments: {str(resp.content)}.")

    environment_ids = [environment_obj["name"] for environment_obj in resp.json()["value"]]
    return environment_ids


def __paginate(
    session: requests.Session, url: str, params: Dict[str, str], endpoint: str, next_link: Optional[str] = None
) -> Generator[Dict[str, Any], None, None]:
    params_to_query = params
    url_to_query = url

    if next_link:
        params_to_query = {}
        url_to_query = next_link

    resp = session.get(url=url_to_query, params=params_to_query)
    if resp.status_code != 200:
        raise RuntimeError(f"Got status code {resp.status_code} for {endpoint}: {str(resp.content)}.")

    res = resp.json()

    yield from res["value"]

    if "nextLink" in res:
        yield from __paginate(session, url, params, endpoint, res["nextLink"])
