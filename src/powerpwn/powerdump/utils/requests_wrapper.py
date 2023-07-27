import logging
import time
from typing import Any, Dict, List, Optional

import requests

from powerpwn.const import LOGGER_NAME, TOOL_NAME

logger = logging.getLogger(LOGGER_NAME)


def init_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers = {"accept": "application/json", "Authorization": token, "User-Agent": TOOL_NAME}
    return session


def consecutive_gets(
    session: requests.Session,
    expected_status_prefix: str = "200",
    property_to_extract_data: str = "value",
    property_for_pagination: str = "continuationToken",
    **kwargs,
):
    value: List[Dict[str, Any]] = []
    success = False
    cont_token = ""  # nosec

    resp_obj = {property_for_pagination: "NOT_EMPTY"}
    while resp_obj.get(property_for_pagination) not in (None, cont_token):
        cont_token = resp_obj.get(property_for_pagination, "")

        success, _, resp_obj = request_and_verify(session=session, expected_status_prefix=expected_status_prefix, method="get", **kwargs)
        if not success:
            break

        if property_to_extract_data not in resp_obj and value != []:
            raise ValueError("Inconsistent responses.")
        if property_to_extract_data not in resp_obj and value == []:
            logger.warning(f"Expected an array response, received an object: {resp_obj}. Request: {kwargs}.")
            success = True
            value += [resp_obj]
        else:
            success = True
            value += resp_obj[property_to_extract_data]

    return success, value


def request_and_verify(session: requests.Session, expected_status_prefix: str = "200", is_json_resp: bool = True, **kwargs):
    success = False
    resp_obj = None
    resp_head = None

    logger.debug(f"Triggering request ({kwargs}).")
    resp = session.request(**kwargs)
    resp_obj = __get_resp_obj(resp) if is_json_resp else resp.text
    if str(resp.status_code).startswith(expected_status_prefix):
        resp_head = resp.headers
        success = True
    else:
        if resp.status_code == 429:
            __handle_throttling(resp_obj)
            return request_and_verify(session, expected_status_prefix, **kwargs)
        logger.info(f"Failed at request ({kwargs}) with status_code={resp.status_code} and content={str(resp.content)}.")

    return success, resp_head, resp_obj


def __get_resp_obj(resp) -> Optional[Dict]:
    resp_obj = None
    try:
        resp_obj = resp.json()
    except requests.exceptions.JSONDecodeError:
        return None

    return resp_obj


def __handle_throttling(resp_obj) -> None:
    message = resp_obj.get("message", "") if resp_obj else ""
    throttling_message_prefix = "Rate limit is exceeded. Try again in "
    if throttling_message_prefix in message:
        seconds_to_wait = int(message.partition(throttling_message_prefix)[2].partition(" seconds")[0])
        logger.info(f"API throttled, going to sleep {seconds_to_wait + 1} before retry")
        time.sleep(seconds_to_wait + 1)
    else:
        time.sleep(20)
