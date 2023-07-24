import json
from typing import List

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.const import ENCODING
from powerpwn.powerdump.utils.requests_wrapper import request_and_verify


class SharedAzureQueuesConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        data_stores: List[DataStore] = []

        # we dont have server/database for another auth types
        if connection_parameters.get("name", "") != "keyBasedAuth":
            return data_stores

        success, _, _ = request_and_verify(session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/testconnection")

        storage_account_name = connection_parameters["values"]["storageaccount"]["value"]

        # if connection is connected with blob endpoint and not storage account
        if storage_account_name.startswith("https://"):
            storage_account_name = "AccountNameFromSettings"  # a hack # connection_parameters["values"]["accountName"]["value"].split(".blob.core.windows.net")[0].partition("https://")[2]

        if success:
            can_list_root_queues, _, queues_val = request_and_verify(
                session=self._session,
                expected_status_prefix="200",
                method="get",
                url=f"{self._root}/v2/storageAccounts/{storage_account_name}/queues/list",
            )
            if can_list_root_queues:
                for queue in queues_val:
                    data_stores.append(
                        DataStore(
                            tenant=None,
                            scope=None,
                            account=storage_account_name,
                            name=queue["Name"],
                            host=f'https://{storage_account_name}.queue.core.windows.net/{queue["Name"]}',
                            extra={},
                        )
                    )

        return data_stores

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        return [
            DataRecord(record_type=DataDumpType.queue_message, record_id=data_store.data_store.name, record_name=data_store.data_store.name, extra={})
        ]

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        queue_name = data_record.data_record.record_id

        success, _, val = request_and_verify(
            session=self._session,
            expected_status_prefix="200",
            method="get",
            url=f"{self._root}/v2/storageAccounts/{data_record.data_store.data_store.account}/queues/{queue_name}/messages?numofmessages=10",
        )

        if not success:
            raise ValueError(
                f"Unable to fetch value for data type: {data_record.data_record.record_type} with ID: {data_record.data_record.record_id}."
            )

        messages = val["QueueMessagesList"]["QueueMessage"]
        document_value = json.dumps(messages).encode(ENCODING)

        data_dump = DataDump(extension="json", encoding=ENCODING, content=document_value)
        return data_dump

    @classmethod
    def api_name(cls) -> str:
        return "shared_azurequeues"

    @classmethod
    def _apim_path(cls) -> str:
        return "azurequeues"
