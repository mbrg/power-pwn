from abc import ABC, abstractmethod
from typing import Generator

import requests

from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase
from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType


class IResourceCollector(ABC):
    @abstractmethod
    def collect(self, session: requests.Session, env_id: str) -> Generator[ResourceEntityBase, None, None]:
        """
        Collect resources

        Args:
            session (requests.Session): authenticated session
            env_id (str): environment id

        """
        ...

    @abstractmethod
    def resource_type(self) -> ResourceType: ...  # noqa
