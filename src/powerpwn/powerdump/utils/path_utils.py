from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType
from powerpwn.powerdump.utils.const import CACHE_PATH


def entities_path(cache_path: str = CACHE_PATH) -> str:
    return f"{cache_path}/resources"


def env_entities_path(env_id: str, cache_path: str = CACHE_PATH) -> str:
    return f"{cache_path}/resources/{env_id}"


def env_entity_type_path(env_id: str, entity_type: ResourceType, cache_path: str = CACHE_PATH) -> str:
    return f"{cache_path}/resources/{env_id}/{entity_type.value}"


def dump_path(cache_path: str = CACHE_PATH) -> str:
    return f"{cache_path}/dump"


def collected_data_path(cache_path: str = CACHE_PATH) -> str:
    return f"{cache_path}/data"


def env_collected_data_path(env_id: str, cache_path: str = CACHE_PATH) -> str:
    return f"{collected_data_path(cache_path)}/{env_id}"


def resource_collected_data_path(env_id: str, resource_id: str, resource_type: ResourceType, cache_path: str = CACHE_PATH) -> str:
    return f"{env_collected_data_path(env_id, cache_path)}/{resource_type}/{resource_id}"
