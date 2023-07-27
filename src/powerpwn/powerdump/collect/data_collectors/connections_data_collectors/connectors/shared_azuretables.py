import json
from typing import List

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.const import ENCODING
from powerpwn.powerdump.utils.requests_wrapper import consecutive_gets, request_and_verify


class SharedAzureTablesConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        data_stores: List[DataStore] = []

        # we dont have server/database for another auth types
        # TODO: create connection with table endpoint instead of account name
        if connection_parameters.get("name", "") != "keyBasedAuth":
            return data_stores

        success, _, _ = request_and_verify(session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/testconnection")

        storage_account_name = connection_parameters["values"]["storageaccount"]["value"]

        # if connection is connected with table endpoint and not storage account
        if storage_account_name.startswith("https://"):
            storage_account_name = "AccountNameFromSettings"  # a hack #connection_parameters["values"]["storageaccount"]["value"].split(".table.core.windows.net")[0].partition("https://")[2]

        if success:
            # TODO: with blob storage endpoint, we are getting Storage account name provided in the authentication 'https://exportdatasa.blob.core.windows.net' doesn't match with storage account name provided in the operation parameter
            data_stores.append(
                DataStore(
                    tenant=None,
                    account=storage_account_name,
                    scope=None,
                    host=f"https://{storage_account_name}.table.core.windows.net",
                    name=storage_account_name,
                    extra={},
                )
            )

        return data_stores

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        data_records: List[DataRecord] = []

        can_list_tables, tables_val = consecutive_gets(
            session=self._session, expected_status_prefix="200", url=f"{self._root}/v2/storageAccounts/{data_store.data_store.name}/tables"
        )
        if can_list_tables:
            for table_obj in tables_val:
                table_name = table_obj["TableName"]
                data_records.append(DataRecord(record_type=DataDumpType.table, record_id=table_name, record_name=table_name, extra={}))

        return data_records

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        table_name = data_record.data_record.record_id
        success, val = consecutive_gets(
            session=self._session,
            expected_status_prefix="200",
            url=f"{self._root}/v2/storageAccounts/{data_record.data_store.data_store.name}/tables/{table_name}/entities",
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
        return "shared_azuretables"

    @classmethod
    def _apim_path(cls) -> str:
        return "azuretables"
