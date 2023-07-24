from typing import List, Set

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_type import DataDumpType
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.const import ENCODING
from powerpwn.powerdump.utils.requests_wrapper import request_and_verify


class GmailConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        success, _, _ = request_and_verify(session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/TestConnection")

        if success:
            return [
                DataStore(
                    tenant=None, account=connection_parameters["accountName"], scope=None, host="https://gmail.googleapis.com/", name=None, extra={}
                )
            ]
        return []

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        data_records: List[DataRecord] = []
        unique_email_ids_seen: Set[str] = set()

        can_list_labels, _, labels_val = request_and_verify(
            session=self._session, expected_status_prefix="200", method="get", url=f"{self._root}/Mail/Labels"
        )
        if can_list_labels:
            # Iterate over parameters to enum as many emails as possible
            for label_obj in labels_val:
                for fetch_only_with_attachments in (True, False):
                    for importance in ("Important", "Not important"):
                        for starred in ("Starred", "Not starred"):
                            params = {
                                "label": label_obj["Id"],
                                "importance": importance,
                                "starred": starred,
                                "fetchOnlyWithAttachments": fetch_only_with_attachments,
                                "includeAttachments": True,
                                "subject": "",
                            }

                            # Iterate over as many subjects as possible
                            get_email_success = True
                            while get_email_success:
                                get_email_success, _, get_email_val = request_and_verify(
                                    session=self._session,
                                    expected_status_prefix="200",
                                    method="get",
                                    url=f"{self._root}/Mail/LastReceived",
                                    params=params,
                                )

                                if get_email_success:
                                    if get_email_val.get("Id") not in unique_email_ids_seen:
                                        data_records.append(
                                            DataRecord(
                                                record_type=DataDumpType.email,
                                                record_id=get_email_val["Id"],
                                                record_name=get_email_val["Subject"],
                                                extra={k: v for k, v in get_email_val.items() if k not in {"Body", "Attachments"}},
                                            )
                                        )

                                        for attachment_obj in get_email_val["Attachments"]:
                                            data_records.append(
                                                DataRecord(
                                                    record_type=DataDumpType.attachment,
                                                    record_id=get_email_val["Id"],
                                                    record_name=attachment_obj["Name"],
                                                    extra={k: v for k, v in attachment_obj.items() if k not in {"ContentBytes"}},
                                                )
                                            )

                                        # avoid processing the same email twice
                                        unique_email_ids_seen.add(get_email_val["Id"])

                                    # Ignore identical subjects to continue iteration
                                    params["subject"] += f" -{get_email_val['Subject']}"

        return data_records

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        if data_record.data_record.record_type == DataDumpType.email:
            success, _, get_email_val = request_and_verify(
                session=self._session,
                expected_status_prefix="200",
                method="get",
                url=f"{self._root}/Mail/{data_record.data_record.record_id}",
                params={"includeAttachments": False},
            )
            if success:
                extension = "html" if data_record.data_record.extra.get("IsHtml", False) else "txt"
                encoding = ENCODING
                content = get_email_val["Body"].encode(ENCODING)

        elif data_record.data_record.record_type == DataDumpType.attachment:
            success, _, get_email_val = request_and_verify(
                session=self._session,
                expected_status_prefix="200",
                method="get",
                url=f"{self._root}/Mail/{data_record.data_record.record_id}",
                params={"includeAttachments": True},
            )

            if success:
                for attachment_obj in get_email_val["Attachments"]:
                    if attachment_obj["Name"] == data_record.data_record.record_name:
                        extension = attachment_obj["ContentType"].partition('name="')[2].partition(".")[-1].replace('"', "")
                        encoding = None
                        content = attachment_obj["ContentBytes"]

                        # We are looking for a specific attachment
                        break
                else:
                    # Couldn't find relevant attachment
                    success = False
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
        return "shared_gmail"

    @classmethod
    def _apim_path(cls) -> str:
        return "gmail"
