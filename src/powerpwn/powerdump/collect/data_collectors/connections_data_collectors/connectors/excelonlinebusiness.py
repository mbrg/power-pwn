import json
from typing import Dict, List

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.const import ENCODING
from powerpwn.powerdump.utils.requests_wrapper import consecutive_gets, request_and_verify


class ExcelOnlineBusinessConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        records: List[DataStore] = []

        sources_success, sources_val = consecutive_gets(
            session=self._session, expected_status_prefix="200", url=f"{self._root}/codeless/v1.0/sources"
        )

        if sources_success:
            for source in sources_val:
                source_id = source["id"]

                params = {"source": source_id}
                drives_success, drives_val = consecutive_gets(
                    session=self._session, expected_status_prefix="200", url=f"{self._root}/codeless/v1.0/drives", params=params
                )

                if drives_success:
                    for drive in drives_val:
                        records.append(
                            DataStore(
                                tenant=None,
                                account=connection_parameters["accountName"],
                                scope=None,
                                host=drive["webUrl"],
                                name=drive["name"],
                                extra={"source": source, "drive": drive},
                            )
                        )

        return records

    def __enum_dir(self, source_id: str, drive_id: str, folder_id: str) -> List[Dict]:
        file_objs: List[Dict] = []

        if folder_id == "root":
            folder_path = "root"
        else:
            folder_path = f"items/{folder_id}"

        params = {"source": source_id}
        can_list_folder, _, list_folder_val = request_and_verify(
            session=self._session,
            expected_status_prefix="200",
            method="get",
            url=f"{self._root}/codeless/v1.0/drives/{drive_id}/{folder_path}/children",
            params=params,
        )
        if can_list_folder:
            if not isinstance(list_folder_val, list):
                raise ValueError(f"Unexpected response list_folder_val: {list_folder_val}.")

            for file_or_dir_obj in list_folder_val:
                if not isinstance(file_or_dir_obj, dict):
                    raise ValueError(f"Unexpected response file_or_dir_obj: {file_or_dir_obj}.")
                if file_or_dir_obj["IsFolder"]:
                    file_objs += self.__enum_dir(source_id=source_id, drive_id=drive_id, folder_id=file_or_dir_obj["Id"])
                else:
                    file_objs += [file_or_dir_obj]

        return file_objs

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        data_records: List[DataRecord] = []

        source_id = data_store.data_store.extra["source"]["id"]
        drive_id = data_store.data_store.extra["drive"]["id"]

        drive_files = self.__enum_dir(source_id=source_id, drive_id=drive_id, folder_id="root")

        for file_obj in drive_files:
            file_id = file_obj["Id"]

            params = {"source": source_id}
            tables_success, tables_val = consecutive_gets(
                session=self._session,
                expected_status_prefix="200",
                url=f"{self._root}/codeless/v1.0/drives/{drive_id}/items/{file_id}/workbook/tables",
                params=params,
            )

            if tables_success:
                for table_obj in tables_val:
                    table_id = table_obj["id"]

                    data_records.append(
                        DataRecord(
                            record_type=DataDumpType.table,
                            record_id=table_id,
                            record_name=f"{file_obj['Path']}/{table_obj['name']}",
                            extra={"file": file_obj, "table": table_obj},
                        )
                    )

        return data_records

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        if data_record.data_record.record_type == DataDumpType.table:
            source_id = data_record.data_store.data_store.extra["source"]["id"]
            drive_id = data_record.data_store.data_store.extra["drive"]["id"]
            file_id = data_record.data_record.extra["file"]["Id"]
            table_id = data_record.data_record.extra["table"]["id"]

            success, rows_val = consecutive_gets(
                session=self._session,
                expected_status_prefix="200",
                url=f"{self._root}/drives/{drive_id}/files/{file_id}/tables/{table_id}/items",
                params={"source": source_id},
            )
            if success:
                extension = "json"
                encoding = ENCODING
                content = json.dumps(rows_val).encode(ENCODING)

        else:
            raise ValueError(f"Unsupported data type: {data_record.data_record.record_type}.")

        if not success:
            raise ValueError(
                f"Unable to fetch value for data type: {data_record.data_record.record_type} with ID: {data_record.data_record.record_id}."
            )

        data_dump = DataDump(extension=extension, encoding=encoding, content=content)
        return data_dump

    @classmethod
    def api_name(cls) -> str:
        return "shared_excelonlinebusiness"

    @classmethod
    def _apim_path(cls) -> str:
        return "excelonlinebusiness"
