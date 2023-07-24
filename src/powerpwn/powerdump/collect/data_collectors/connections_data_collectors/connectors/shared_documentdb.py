import json
from typing import List

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.const import ENCODING
from powerpwn.powerdump.utils.requests_wrapper import consecutive_gets, request_and_verify


class SharedDocumentDBConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        data_stores: List[DataStore] = []

        # we dont have server/database for another auth types
        if connection_parameters.get("name", "") != "keyBasedAuth":
            return data_stores

        success, _, _ = request_and_verify(session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/testconnection")

        db_name = connection_parameters["values"]["databaseAccount"]["value"]

        if success:
            data_stores.append(
                DataStore(tenant=None, account="temp", scope=None, host=f"https://{db_name}.table.cosmos.azure.com:443/", name=db_name, extra={})
            )

        return data_stores

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        data_records: List[DataRecord] = []

        can_list_databases, databases_val = consecutive_gets(
            session=self._session,
            expected_status_prefix="200",
            property_to_extract_data="Databases",
            url=f"{self._root}/v2/cosmosdb/{data_store.data_store.name}/dbs",
        )
        if can_list_databases:
            for db_obj in databases_val:
                db_name = db_obj["id"]

                can_list_collections, collections_val = consecutive_gets(
                    session=self._session,
                    expected_status_prefix="200",
                    property_to_extract_data="DocumentCollections",
                    url=f"{self._root}/v2/cosmosdb/{data_store.data_store.name}/dbs/{db_name}/colls",
                )
                if can_list_collections:
                    for collection in collections_val:
                        data_records.append(
                            DataRecord(
                                record_type=DataDumpType.collection,
                                record_id=collection["id"],
                                record_name=f'{db_name}-{collection["id"]}',
                                extra={"db_name": db_name},
                            )
                        )

        return data_records

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        db_name = data_record.data_record.extra["db_name"]
        success, val = consecutive_gets(
            session=self._session,
            expected_status_prefix="200",
            property_to_extract_data="Documents",
            url=f"{self._root}/v2/cosmosdb/{data_record.data_store.data_store.name}/dbs/{db_name}/colls/{data_record.data_record.record_id}/docs",
        )

        if not success:
            raise ValueError(
                f"Unable to fetch value for data type: {data_record.data_record.record_type} with ID: {data_record.data_record.record_id}."
            )

        document_value = json.dumps(val).encode(ENCODING)

        data_dump = DataDump(extension="json", encoding=ENCODING, content=document_value)
        return data_dump

    @classmethod
    def api_name(cls) -> str:
        return "shared_documentdb"

    @classmethod
    def _apim_path(cls) -> str:
        return "documentdb"
