import logging
from typing import Dict, Generator, List

import requests

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.powerdump.collect.models.connector_entity import Connector
from powerpwn.powerdump.collect.resources_collectors._api import get_connector
from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType
from powerpwn.powerdump.collect.resources_collectors.iresource_collector import IResourceCollector
from powerpwn.powerdump.utils.const import SPEC_JWT_NAME

logger = logging.getLogger(LOGGER_NAME)


class ConnectorsCollector(IResourceCollector):
    def __init__(self, connector_id_to_connection_ids: Dict[str, List[str]]) -> None:
        self.__connector_id_to_connection_ids = connector_id_to_connection_ids

    def collect(self, session: requests.Session, environment_id: str) -> Generator[Connector, None, None]:
        for connector_id in self.__connector_id_to_connection_ids:
            logger.info(f"Fetching OpenAPI spec for connector {connector_id}.")

            try:
                connector = get_connector(session, environment_id=environment_id, connector_id=connector_id)
            except RuntimeError as e:
                if "403" in str(e):
                    logger.warning(f"User doesn't have access to custom connector spec for connector_id={connector_id}. Skipping spec.")
                    continue
                elif "400" in str(e):
                    logger.error(f"Failed to get connector {connector_id} for connection {self.__connector_id_to_connection_ids[connector_id]}")
                    continue
                raise e

            swagger = connector["properties"]["swagger"]

            swagger["securityDefinitions"] = swagger.get("securityDefinitions", {})
            swagger["securityDefinitions"][SPEC_JWT_NAME] = {
                "name": "Authorization",
                "in": "header",
                "type": "apiKey",
                "description": "JWT Authorization header",
            }

            swagger["security"] = swagger.get("security", [])
            swagger["security"].append({"ApiHubBearerAuth": []})

            spec = Connector(
                api_name=connector_id,
                display_name=connector_id,
                environment_id=environment_id,
                created_at=connector["properties"]["createdTime"],
                last_modified_at=connector["properties"]["changedTime"],
                created_by=connector["properties"]["publisher"],
                version=connector["properties"]["swagger"]["info"]["version"],
                swagger=swagger,
                entity_id=connector_id,
                entity_type=ResourceType.connector,
                raw_json=connector,
            )

            yield spec

    def resource_type(self) -> ResourceType:
        return ResourceType.connector
