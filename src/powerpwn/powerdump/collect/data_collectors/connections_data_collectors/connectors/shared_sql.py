import json
from typing import List

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.const import ENCODING
from powerpwn.powerdump.utils.requests_wrapper import consecutive_gets, request_and_verify


class SharedSqlConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        data_stores: List[DataStore] = []

        # we dont have server/database for another auth types
        # if we use the /servers endpoint for other auth types we will get []
        if not (
            connection_parameters.get("name", "") in ("sqlAuthentication", "windowsAuthentication")
            or connection_parameters.get("authType", "") == "windows"
        ):
            return data_stores

        is_windows = connection_parameters.get("authType", "") == "windows"

        success, _, _ = request_and_verify(session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/testconnection")

        if success:
            data_stores.append(
                DataStore(
                    tenant=None,
                    account="temp",
                    scope=None,
                    host=(
                        f'https://{connection_parameters["server"]}.database.windows.net'
                        if is_windows
                        else f'https://{connection_parameters["values"]["server"]["value"]}'
                    ),
                    name=connection_parameters["server"] if is_windows else connection_parameters["values"]["server"]["value"],
                    extra={},
                )
            )

        return data_stores

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        data_records: List[DataRecord] = []

        can_list_databases, databases_val = consecutive_gets(
            session=self._session, expected_status_prefix="200", url=f"{self._root}/v2/databases?server={data_store.data_store.name}"
        )
        if can_list_databases:
            for db_obj in databases_val:
                db_name = db_obj["Name"]

                can_list_tables, tables_val = consecutive_gets(
                    session=self._session, expected_status_prefix="200", url=f"{self._root}/v2/datasets/{data_store.data_store.name},{db_name}/tables"
                )
                if can_list_tables:
                    for table in tables_val:
                        table_display_name = table["DisplayName"]
                        data_records.append(
                            DataRecord(
                                record_type=DataDumpType.table,
                                record_id=table["Name"],
                                record_name=f"{db_name}-{table_display_name}",
                                extra={"db_name": db_name},
                            )
                        )

        return data_records

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        server_name = data_record.data_store.data_store.name
        db_name = data_record.data_record.extra["db_name"]
        success, val = consecutive_gets(
            session=self._session,
            expected_status_prefix="200",
            url=f"{self._root}/v2/datasets/{server_name},{db_name}/tables/{data_record.data_record.record_id}/items",
        )

        if not success:
            raise ValueError(
                f"Unable to fetch value for data type: {data_record.data_record.record_type} with ID: {data_record.data_record.record_id}."
            )

        table_value = json.dumps(val).encode(ENCODING)

        data_dump = DataDump(extension="json", encoding=ENCODING, content=table_value)
        return data_dump

    @classmethod
    def api_name(cls) -> str:
        return "shared_sql"

    @classmethod
    def _apim_path(cls) -> str:
        return "sql"
