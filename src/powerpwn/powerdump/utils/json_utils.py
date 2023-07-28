"""
Copied from AFK
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.powerdump.collect.models.base_entity import BaseEntity

logger = logging.getLogger(LOGGER_NAME)


def _flatten_nested_dict(val: Any, prefix: str = "") -> List[Tuple[Any, Any]]:
    res = []
    if isinstance(val, (str, int, float, bool)) or val is None:
        res.append((val, prefix))
    elif isinstance(val, dict):
        for k in val.keys():
            res.extend(_flatten_nested_dict(val[k], f"{prefix}.{k}"))
    elif isinstance(val, (list, tuple)):
        for i in range(len(val)):
            res.extend(_flatten_nested_dict(val[i], f"{prefix}.{i}"))
    elif isinstance(val, BaseEntity):
        res.extend(_flatten_nested_dict(json.loads(val.json()), prefix))
    else:
        raise ValueError(f"Unsupported type {type(val)}.")
    return res


def flatten_nested_dict(val: Any) -> Dict[Any, Any]:
    """
    Flatten nested dict recursively
    @param val: nested dict
    @return: flattened dict
    """
    res = _flatten_nested_dict(val)
    return {key: val for val, key in res}


def deep_compare_nested_dict(val_one: Any, val_two: Any, allow_additional_keys: bool = False) -> bool:
    """
    Compare nested dict recursively
    @param val_one: first nested dict
    @param val_two: second nested dict
    @param allow_additional_keys: if True, val_one and val_two are allowed to contains nested properties that are not present in the other.
    @return: whether the two dicts are equal in all nested properties
    """
    val_one_flat = flatten_nested_dict(val_one)
    val_two_flat = flatten_nested_dict(val_two)

    val_one_key_set = set(val_one_flat.keys())
    val_two_key_set = set(val_two_flat.keys())

    missing_key_from_val_one = val_one_key_set.difference(val_two_key_set)
    if len(missing_key_from_val_one) > 0:
        logger.debug(f"val_two is missing the following elements from val_one: {missing_key_from_val_one}.")
        if not allow_additional_keys:
            return False

    missing_key_from_val_two = val_two_key_set.difference(val_one_key_set)
    if len(missing_key_from_val_two) > 0:
        logger.debug(f"val_one is missing the following elements from val_two: {missing_key_from_val_two}.")
        if not allow_additional_keys:
            return False

    mutual_keys = val_one_key_set.intersection(val_two_key_set)
    for k in mutual_keys:
        # pydantic and json load can change type of int, bool and more from str
        if not json_consistent_compare(val_one_flat[k], val_two_flat[k]):
            logger.debug(f"Value for key {k} does not align.")
            return False

    return True


def json_consistent_compare(val_one: Optional[Union[str, int, bool, float]], val_two: Optional[Union[str, int, bool, float]]) -> bool:
    """
    Compares values in a way consistent with json dump and load.
    I.e, json_consistent_compare(val, json.loads(json.dumps(val))) is True.
    @param val_one: value to compare.
    @param val_two: value to compare.
    @return: whether the two values are equal in a way consistent with json dump and load.
    """
    if isinstance(val_one, type(val_two)) or isinstance(val_one, bool) or isinstance(val_two, bool):
        return val_one == val_two
    elif isinstance(val_one, str) or isinstance(val_two, str):
        return str(val_one) == str(val_two)
    elif isinstance(val_one, str) or isinstance(val_two, str):
        return str(val_one) == str(val_two)
    elif isinstance(val_one, int) and isinstance(val_two, float):
        return float(val_one) == val_two
    elif isinstance(val_two, int) and isinstance(val_one, float):
        return float(val_two) == val_one
    else:
        raise ValueError(f"Unsupported type combination {type(val_one)}, {type(val_one)}.")


def change_obj_recu(val: Any, obj_changer: Callable[[dict], None]) -> None:
    if isinstance(val, (str, int, float, bool)) or val is None:
        return
    elif isinstance(val, dict):
        obj_changer(val)

        for k in val.keys():
            change_obj_recu(val[k], obj_changer=obj_changer)
    elif isinstance(val, (list, tuple)):
        for i in range(len(val)):
            change_obj_recu(val[i], obj_changer=obj_changer)
    elif isinstance(val, BaseEntity):
        change_obj_recu(val.json(), obj_changer=obj_changer)
    else:
        raise ValueError(f"Unsupported type {type(val)}.")
