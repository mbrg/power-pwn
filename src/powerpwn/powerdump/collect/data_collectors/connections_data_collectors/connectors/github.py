from typing import List

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors.connector_base import ConnectorBase
from powerpwn.powerdump.collect.models.data_dump_entity import DataDump
from powerpwn.powerdump.collect.models.data_record_entity import DataRecord, DataRecordWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStore, DataStoreWithContext
from powerpwn.powerdump.utils.requests_wrapper import request_and_verify


class GitHubConnector(ConnectorBase):
    def _ping(self, connection_parameters: dict) -> List[DataStore]:
        records: List[DataStore] = []

        # while spec documents status_code 200 on success, 202 has been observed as well
        success, head, val = request_and_verify(
            session=self._session, expected_status_prefix="20", method="get", url=f"{self._root}/trigger/issueClosed"
        )

        if success:
            records.append(
                DataStore(
                    tenant=None, account=head["x-oauth-client-id"], scope=head["x-oauth-scopes"], host="https://api.github.com/", name=None, extra={}
                )
            )

        return records

    def _enum(self, data_store: DataStoreWithContext) -> List[DataRecord]:
        raise NotImplementedError()

    def _dump(self, data_record: DataRecordWithContext) -> DataDump:
        raise NotImplementedError()

    @classmethod
    def api_name(cls) -> str:
        return "shared_github"

    @classmethod
    def _apim_path(cls) -> str:
        return "github"

    @classmethod
    def uses_undocumented_api_properties(cls) -> bool:
        # headers returned from the API are not documented in the swagger
        return True
