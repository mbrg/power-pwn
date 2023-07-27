import abc
from typing import List

import requests

from powerpwn.powerdump.collect.models.connector_entity import Connector
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump, DataDumpWithContext
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext


class ConnectorBase(abc.ABC):
    def __init__(self, session: requests.Session, spec: Connector, connection_id: str):
        self._session = session
        self._environment_id = spec.environment_id
        self._connection_id = connection_id

        host = spec.swagger["host"]
        base_path = spec.swagger["basePath"]
        self._root = f"https://{host}{base_path}/{connection_id}"

    def ping(self, connection_parameters: dict) -> List[DataStoreWithContext]:
        """
        Test connection to api

        Args:
            connection_parameters (dict): connection parameters to api

        Returns:
            list[DataStoreWithContext]: list of data store entities to query
        """
        return [
            DataStoreWithContext(api_name=self.api_name(), connection_id=self._connection_id, data_store=data_store)
            for data_store in self._ping(connection_parameters=connection_parameters)
        ]

    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        pass

    def enum(self, data_store: DataStoreWithContext) -> List[DataRecordWithContext]:
        return [DataRecordWithContext(data_store=data_store, data_record=data_record) for data_record in self._enum(data_store=data_store)]

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        pass

    def dump(self, data_record: DataRecordWithContext) -> DataDumpWithContext:
        """
        Dump data

        Args:
            data_record (DataRecordWithContext): data record details to dump

        Returns:
            DataDumpWithContext: dump data
        """
        return DataDumpWithContext(data_record=data_record, data_dump=self._dump(data_record=data_record))

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        pass

    @classmethod
    def api_name(cls) -> str:
        pass

    @classmethod
    def _apim_path(cls) -> str:
        pass

    @classmethod
    def uses_undocumented_api_properties(cls) -> bool:
        return False
