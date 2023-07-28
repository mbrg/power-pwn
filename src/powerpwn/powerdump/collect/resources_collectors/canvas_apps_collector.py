import logging
from typing import Generator

import requests

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.powerdump.collect.models.canvas_app_entity import CanvasApp
from powerpwn.powerdump.collect.models.principal_entity import Principal
from powerpwn.powerdump.collect.resources_collectors._api import list_canvas_app_rbac, list_canvas_apps
from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType
from powerpwn.powerdump.collect.resources_collectors.iresource_collector import IResourceCollector

logger = logging.getLogger(LOGGER_NAME)


class CanvasAppsCollector(IResourceCollector):
    def collect(self, session: requests.Session, environment_id: str) -> Generator[CanvasApp, None, None]:
        total_canvas_apps = 0
        total_widely_shared_canvas_apps = 0
        for canvas_app in list_canvas_apps(session, environment_id):
            total_canvas_apps += 1
            rbacs = list(list_canvas_app_rbac(session, canvas_app["name"], environment_id))
            if any(rbac.get("properties", {}).get("principal", {}).get("type", "NOT_TENANT") == "Tenant" for rbac in rbacs):
                total_widely_shared_canvas_apps += 1
                principals = []
                for rbac in rbacs:
                    if rbac["properties"]["principal"]["type"] == "Tenant":
                        principals.append(
                            Principal(
                                entity_type=ResourceType.principal,
                                entity_id=rbac["properties"]["principal"].get("tenantId"),
                                principal_id=rbac["properties"]["principal"].get("tenantId"),
                                type=rbac["properties"]["principal"].get("type"),
                                tenant_id=rbac["properties"]["principal"].get("tenantId"),
                                raw_json=rbac,
                                display_name=rbac["properties"]["principal"].get("tenantId"),
                            )
                        )
                    else:
                        principals.append(
                            Principal(
                                entity_type=ResourceType.principal,
                                entity_id=rbac["properties"]["principal"].get("id"),
                                principal_id=rbac["properties"]["principal"].get("id"),
                                type=rbac["properties"]["principal"].get("type"),
                                tenant_id=rbac["properties"]["principal"].get("tenantId", "N/A"),
                                display_name=rbac["properties"]["principal"].get("displayName"),
                                email=rbac["properties"]["principal"].get("email"),
                                upn=rbac["properties"]["principal"].get("email"),
                                raw_json=rbac,
                            )
                        )

                created_by = Principal(
                    entity_type=ResourceType.principal,
                    entity_id=canvas_app["properties"]["createdBy"].get("id"),
                    principal_id=canvas_app["properties"]["createdBy"].get("id"),
                    type=canvas_app["properties"]["createdBy"].get("type"),
                    tenant_id=canvas_app["properties"]["createdBy"].get("tenantId", "N/A"),
                    display_name=canvas_app["properties"]["createdBy"].get("displayName"),
                    email=canvas_app["properties"]["createdBy"].get("email"),
                    upn=canvas_app["properties"]["createdBy"].get("userPrincipalName"),
                    raw_json=canvas_app["properties"]["createdBy"],
                )

                run_url = canvas_app["properties"]["appPlayUri"]
                version = canvas_app["properties"]["appVersion"]
                environment_id = canvas_app["properties"]["environment"]["name"].replace("default", "Default")

                yield CanvasApp(
                    raw_json=canvas_app,
                    display_name=canvas_app["properties"]["displayName"],
                    created_by=created_by,
                    created_at=canvas_app["properties"]["createdTime"],
                    last_modified_at=canvas_app["properties"]["lastModifiedTime"],
                    run_url=run_url,
                    version=version,
                    permissions=principals,
                    entity_id=canvas_app["name"],
                    environment_id=environment_id,
                    entity_type=ResourceType.canvas_app,
                )
        logger.info(
            f"Found {total_widely_shared_canvas_apps} widely shared canvas apps out of {total_canvas_apps} canvas apps in environment {environment_id}"
        )

    def resource_type(self) -> ResourceType:
        return ResourceType.canvas_app
