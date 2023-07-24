import urllib.parse
from typing import Any, Dict, Generator, List

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.const import ENCODING
from powerpwn.powerdump.utils.requests_wrapper import consecutive_gets, request_and_verify


class SharedAzureBlobConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        data_stores: List[DataStore] = []

        # we dont have server/database for another auth types
        if connection_parameters.get("name", "") != "keyBasedAuth":
            return data_stores

        success, _, _ = request_and_verify(session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/testconnection")

        storage_account_name = connection_parameters["values"]["accountName"]["value"]

        # if connection is connected with blob endpoint and not storage account
        if storage_account_name.startswith("https://"):
            storage_account_name = "AccountNameFromSettings"  # a hack # connection_parameters["values"]["accountName"]["value"].split(".blob.core.windows.net")[0].partition("https://")[2]

        if success:
            # TODO: with blob storage endpoint, we are getting Storage account name provided in the authentication 'https://exportdatasa.blob.core.windows.net' doesn't match with storage account name provided in the operation parameter
            can_list_root_folders, root_folders_val = consecutive_gets(
                session=self._session,
                expected_status_prefix="200",
                property_for_pagination="nextLink",
                url=f"{self._root}/v2/datasets/{storage_account_name}/foldersV2",
            )
            if can_list_root_folders:
                for root_folder in root_folders_val:
                    data_stores.append(
                        DataStore(
                            tenant=None,
                            scope=None,
                            account=storage_account_name,
                            name=root_folder["DisplayName"],
                            host=f'https://{storage_account_name}.blob.core.windows.net/{root_folder["Name"]}',
                            extra={"storage_account_name": storage_account_name, "blob_id": root_folder["Id"]},
                        )
                    )

        return data_stores

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        data_records: List[DataRecord] = []
        folder_obj = {"Id": data_store.data_store.extra["blob_id"], "IsFolder": True}
        files = self.__enumerate_folders_content_recursively(data_store.data_store.extra["storage_account_name"], folder_obj)
        for file_obj in files:
            data_records.append(
                DataRecord(
                    record_type=DataDumpType.file,
                    record_id=file_obj["Id"],
                    record_name=file_obj["Name"],
                    extra={"file_path": file_obj["Path"], "media_type": file_obj["MediaType"]},
                )
            )

        return data_records

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        file_id = urllib.parse.quote(data_record.data_record.record_id)

        success, _, val = request_and_verify(
            session=self._session,
            expected_status_prefix="200",
            is_json_resp=False,
            method="get",
            url=f"{self._root}/v2/datasets/{data_record.data_store.data_store.extra['storage_account_name']}/files/{file_id}/content",
        )

        if not success:
            raise ValueError(
                f"Unable to fetch value for data type: {data_record.data_record.record_type} with ID: {data_record.data_record.record_id}."
            )

        document_value = val.encode(ENCODING)

        # add check for mypy
        if file_name := data_record.data_record.record_name:
            extension = file_name.split(".")[-1]

            last_index_for_extension = file_name.rindex(".")
            data_record.data_record.record_name = file_name[:last_index_for_extension]

        data_dump = DataDump(extension=extension, encoding=ENCODING, content=document_value)
        return data_dump

    def __enumerate_folders_content_recursively(self, storage_account: str, root_folder: Dict[str, str]) -> Generator[Dict[str, Any], None, None]:
        stack = [root_folder]
        while len(stack) > 0:
            current_folder_obj = stack.pop()
            if not current_folder_obj["IsFolder"]:
                yield current_folder_obj
            else:
                current_folder_obj_id = current_folder_obj["Id"]
                # TODO: use right pagination method with nextLink
                is_success, sub_folders = consecutive_gets(
                    session=self._session,
                    expected_status_prefix="200",
                    property_for_pagination="nextLink",
                    url=f"{self._root}/v2/datasets/{storage_account}/foldersV2/{current_folder_obj_id}",
                )
                if is_success and len(sub_folders) > 0:
                    stack.extend(sub_folders)

    @classmethod
    def api_name(cls) -> str:
        return "shared_azureblob"

    @classmethod
    def _apim_path(cls) -> str:
        return "azureblob"
