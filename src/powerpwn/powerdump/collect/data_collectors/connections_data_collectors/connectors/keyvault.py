from typing import List

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.const import ENCODING
from powerpwn.powerdump.utils.requests_wrapper import consecutive_gets, request_and_verify


class KeyVaultConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        data_stores: List[DataStore] = []

        can_list_keys, _, _ = request_and_verify(session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/keys")
        can_list_secrets, _, _ = request_and_verify(session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/secrets")

        if can_list_keys or can_list_secrets:
            if (account := connection_parameters.get("accountName")) is not None:
                pass
            elif (account := connection_parameters.get("token:clientId")) is not None:
                pass
            else:
                raise ValueError(f"Couldn't find expected connection parameters. Got: {connection_parameters.keys()}.")

            data_stores.append(
                DataStore(
                    tenant=connection_parameters.get("token:TenantId"),
                    account=account,
                    scope=None,
                    host=f"https://{connection_parameters['vaultName'].strip(' ')}.vault.azure.net/",
                    name=connection_parameters["vaultName"],
                    extra={},
                )
            )

        return data_stores

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        data_records: List[DataRecord] = []

        can_list_keys, keys_val = consecutive_gets(session=self._session, expected_status_prefix="200", url=f"{self._root}/keys")
        if can_list_keys:
            for key_obj in keys_val:
                data_records.append(DataRecord(record_type=DataDumpType.key, record_id=key_obj["name"], record_name=key_obj["name"], extra=key_obj))

        can_list_secrets, secrets_val = consecutive_gets(session=self._session, expected_status_prefix="200", url=f"{self._root}/secrets")
        if can_list_secrets:
            for secret_obj in secrets_val:
                data_records.append(
                    DataRecord(record_type=DataDumpType.secret, record_id=secret_obj["name"], record_name=secret_obj["name"], extra=secret_obj)
                )

        return data_records

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        if data_record.data_record.record_type == DataDumpType.key:
            raise NotImplementedError("Dumping key value has not been implemented.")
        elif data_record.data_record.record_type == DataDumpType.secret:
            success, _, val = request_and_verify(
                session=self._session,
                expected_status_prefix="200",
                method="get",
                url=f"{self._root}/secrets/{data_record.data_record.record_id}/value",
            )
        else:
            raise ValueError(f"Unsupported data type: {data_record.data_record.record_type}.")

        if not success:
            raise ValueError(
                f"Unable to fetch value for data type: {data_record.data_record.record_type} with ID: {data_record.data_record.record_id}."
            )

        secret_value: str = val["value"]

        data_dump = DataDump(extension="txt", encoding=ENCODING, content=secret_value.encode(ENCODING))
        return data_dump

    @classmethod
    def api_name(cls) -> str:
        return "shared_keyvault"

    @classmethod
    def _apim_path(cls) -> str:
        return "keyvault"
