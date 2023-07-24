import logging
from typing import Dict, Generator, List

import requests

from powerpwn.const import LOGGER_NAME
from powerpwn.powerdump.collect.models.connection_entity import Connection
from powerpwn.powerdump.collect.models.principal_entity import Principal
from powerpwn.powerdump.collect.resources_collectors._api import list_connections
from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType
from powerpwn.powerdump.collect.resources_collectors.iresource_collector import IResourceCollector

logger = logging.getLogger(LOGGER_NAME)


class ConnectionsCollector(IResourceCollector):
    def __init__(self, connector_id_to_connection_ids: Dict[str, List[str]]) -> None:
        self.__connector_id_to_connection_ids = connector_id_to_connection_ids

    def collect(self, session: requests.Session, environment_id: str) -> Generator[Connection, None, None]:
        total_connections_count = 0
        active_shareable_connections_count = 0
        raw_connections = list_connections(session, environment_id=environment_id)

        for raw_connection in raw_connections:
            total_connections_count += 1
            if raw_connection["properties"]["apiId"] != "/providers/Microsoft.PowerApps/apis/shared_logicflows" and (
                raw_connection["properties"]["statuses"][0]["status"] != "Connected" or not raw_connection["properties"]["allowSharing"]
            ):
                # ignore non-active or non shareable connections, other than Logic Flows
                continue

            active_shareable_connections_count += 1
            principal = Principal(
                entity_type=ResourceType.principal,
                entity_id=raw_connection["properties"]["createdBy"].get("id"),
                principal_id=raw_connection["properties"]["createdBy"].get("id"),
                type=raw_connection["properties"]["createdBy"].get("type"),
                tenant_id=raw_connection["properties"]["createdBy"].get("tenantId", "N/A"),
                display_name=raw_connection["properties"]["createdBy"].get("displayName"),
                email=raw_connection["properties"]["createdBy"].get("email"),
                upn=raw_connection["properties"]["createdBy"].get("userPrincipalName"),
                raw_json=raw_connection["properties"]["createdBy"],
            )

            connection_props = {
                "accountName": raw_connection["properties"].get("accountName"),
                **raw_connection["properties"].get("connectionParameters", {}),
                **raw_connection["properties"].get("connectionParametersSet", {}),
            }

            connection = Connection(
                entity_type=ResourceType.connection,
                entity_id=raw_connection["name"],
                connection_id=raw_connection["name"],
                display_name=raw_connection["properties"]["displayName"],
                is_valid=all([status_obj["status"] == "Connected" for status_obj in raw_connection["properties"]["statuses"]]),
                connector_id=raw_connection["properties"]["apiId"].replace("/providers/Microsoft.PowerApps/apis/", ""),
                api_id=raw_connection["properties"]["apiId"],
                icon_uri=raw_connection["properties"]["iconUri"],
                environment_id=raw_connection["properties"]["environment"]["id"]
                .replace("/providers/Microsoft.PowerApps/environments/", "")
                .replace("default", "Default"),
                environment_name=raw_connection["properties"]["environment"]["name"],
                created_at=raw_connection["properties"]["createdTime"],
                last_modified_at=raw_connection["properties"]["lastModifiedTime"],
                expiration_time=raw_connection["properties"].get("expirationTime"),
                created_by=principal,
                connection_parameters=connection_props,
                test_uri=raw_connection["properties"].get("testLinks", [{}])[0].get("requestUri"),
                raw_json=raw_connection,
            )

            self.__connector_id_to_connection_ids[connection.connector_id] = self.__connector_id_to_connection_ids.get(
                connection.connector_id, []
            ) + [connection.connection_id]

            yield connection
        logger.info(
            f"Found {active_shareable_connections_count} active shareable connections out of {total_connections_count} connections in environment {environment_id}"
        )

    def resource_type(self) -> ResourceType:
        return ResourceType.connection
