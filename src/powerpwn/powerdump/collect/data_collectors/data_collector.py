import os
import shutil

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connections_data_collector import ConnectionsDataCollector
from powerpwn.powerdump.utils.model_loaders import get_environment_ids
from powerpwn.powerdump.utils.path_utils import env_collected_data_path
from powerpwn.powerdump.utils.requests_wrapper import init_session


class DataCollector:
    """
    A Class to collect data from resources and cache them in provided cache path
    """

    def __init__(self, cache_path: str, token: str) -> None:
        self.__cache_path = cache_path
        self.__session = init_session(token=token)
        self.__data_collectors = [ConnectionsDataCollector]

    def collect(self) -> bool:
        environment_ids = get_environment_ids(self.__cache_path)
        if len(environment_ids) == 0:
            return False

        for env_id in get_environment_ids(self.__cache_path):
            env_dumps_root_dir = env_collected_data_path(env_id, self.__cache_path)
            if os.path.isdir(env_dumps_root_dir):
                shutil.rmtree(env_dumps_root_dir)

            for data_collector in self.__data_collectors:
                data_collector_instance = data_collector(self.__cache_path)
                data_collector_instance.collect(self.__session, env_id, env_dumps_root_dir)
        return True
