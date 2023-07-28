import logging
import os.path
from typing import Dict, Generator, List

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase
from powerpwn.powerdump.collect.resources_collectors._api import list_environments
from powerpwn.powerdump.collect.resources_collectors.canvas_apps_collector import CanvasAppsCollector
from powerpwn.powerdump.collect.resources_collectors.connections_collector import ConnectionsCollector
from powerpwn.powerdump.collect.resources_collectors.connectors_collector import ConnectorsCollector
from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType
from powerpwn.powerdump.utils.const import DATA_MODEL_FILE_EXTENSION
from powerpwn.powerdump.utils.path_utils import env_entity_type_path
from powerpwn.powerdump.utils.requests_wrapper import init_session

logger = logging.getLogger(LOGGER_NAME)


class ResourcesCollector:
    """
    A Class to collect resources and cache them in provided cache path
    """

    def __init__(self, cache_path: str, token: str) -> None:
        self.__cache_path = cache_path
        self.__session = init_session(token=token)
        self.__collectors = [CanvasAppsCollector, ConnectionsCollector, ConnectorsCollector]

    def collect_and_cache(self) -> None:
        """
        Collect resources and store them in cache

        Args:
            cache_path (str): cache path to store resources
        """
        environment_ids = list_environments(self.__session)
        logger.info(f"Found {len(environment_ids)} environments.")

        for env_id in environment_ids:
            connector_id_to_connection_ids: Dict[str, List[str]] = dict()
            for collector in self.__collectors:
                if collector in (ConnectionsCollector, ConnectorsCollector):
                    collector_instance = collector(connector_id_to_connection_ids)
                else:
                    collector_instance = collector()
                self._cache_entities(collector_instance.collect(self.__session, env_id), collector_instance.resource_type(), env_id)

    def _cache_entities(self, entities: Generator[ResourceEntityBase, None, None], entity_type: ResourceType, env_id: str) -> None:
        dir_name = env_entity_type_path(env_id, entity_type, self.__cache_path)
        os.makedirs(dir_name, exist_ok=True)
        for entity in entities:
            file_path = os.path.join(dir_name, entity.entity_id + DATA_MODEL_FILE_EXTENSION)
            with open(file_path, "w") as fp:
                fp.write(entity.json())
