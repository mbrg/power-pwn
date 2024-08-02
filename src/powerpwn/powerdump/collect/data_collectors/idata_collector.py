from abc import ABC, abstractmethod

import requests


class IDataCollector(ABC):
    @abstractmethod
    def collect(self, session: requests.Session, env_id: str, output_dir: str) -> None:
        ...  # noqa
