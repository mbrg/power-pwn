import json
import os
import pathlib
from typing import Optional

from flask import Flask, render_template
from swagger_ui import flask_api_doc

from powerpwn.cli.const import TOOL_NAME
from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase
from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType
from powerpwn.powerdump.utils.model_loaders import (
    get_canvasapp,
    get_connection,
    get_connector,
    load_canvasapps,
    load_connections,
    load_connectors,
    load_resources,
    map_connector_id_and_env_id_to_connection_ids,
)


def register_specs(app: Flask, cache_path: str):
    connections = load_connections(cache_path=cache_path)
    connector_id_and_env_id_to_connection_ids = map_connector_id_and_env_id_to_connection_ids(connections=connections)

    for spec in load_connectors(cache_path=cache_path):
        # clean connectionId from parameters
        for _, path_obj in spec.swagger.get("paths", {}).items():
            for _, path_method_obj in path_obj.items():
                path_method_obj["parameters"] = [params for params in path_method_obj.get("parameters", []) if params.get("name") != "connectionId"]

        # generate Swagger UI for each connection
        for connection_id in connector_id_and_env_id_to_connection_ids[(spec.api_name, spec.environment_id)]:
            title = f"{spec.swagger['info']['title']} / {connection_id}"
            base_path = spec.swagger["basePath"].replace("/apim/", "")

            flask_api_doc(
                app,
                config=spec.processed_swagger(connection_id=connection_id, make_concrete=False),
                url_prefix=f"/api/shared_{base_path}/{connection_id}",
                title=title,
            )


def full_resources_table_wrapper(cache_path: str):
    def full_resources_table():
        resources = list(load_resources(cache_path=cache_path))

        return render_template("resources_table.html", title=TOOL_NAME, resources=resources)

    return full_resources_table


def full_connection_table_wrapper(cache_path: str):
    def full_connection_table():
        connections = list(load_connections(cache_path=cache_path))

        return render_template("connections_table.html", title=f"{TOOL_NAME} - Connections", resources=connections)

    return full_connection_table


def flt_connection_table_wrapper(cache_path: str):
    def flt_connection_table(connector_id: str):
        connections = [conn for conn in load_connections(cache_path=cache_path) if conn.connector_id == connector_id]

        return render_template("connections_table.html", title=f"{TOOL_NAME} - {connector_id}", resources=connections)

    return flt_connection_table


def full_canvasapps_table_wrapper(cache_path: str):
    def full_canvasapp_table():
        apps = list(load_canvasapps(cache_path=cache_path))

        return render_template("canvasapps_table.html", title=f"{TOOL_NAME} - Canvas Apps", resources=apps)

    return full_canvasapp_table


def full_connectors_table_wrapper(cache_path: str):
    def full_connector_table():
        connectors = list(load_connectors(cache_path=cache_path))

        return render_template("connectors_table.html", title=f"{TOOL_NAME} - Connectors", resources=connectors)

    return full_connector_table


def flt_resource_wrapper(cache_path: str):
    def get_resource_page(resource_type: ResourceType, env_id: str, resource_id: str):
        resource: Optional[ResourceEntityBase] = None
        if resource_type == ResourceType.canvas_app:
            resource = get_canvasapp(cache_path, env_id, resource_id)
        elif resource_type == ResourceType.connection:
            resource = get_connection(cache_path, env_id, resource_id)
        elif resource_type == ResourceType.connector:
            resource = get_connector(cache_path, env_id, resource_id)

        if resource:
            return render_template(
                "json_object.html", title=f"{TOOL_NAME} - {resource_type} {resource_id}", json_object=json.dumps(resource.raw_json)
            )

    return get_resource_page


def __get_template_full_path(template_name: str) -> str:
    return os.path.join(pathlib.Path(__file__).parent.resolve(), "templates", template_name)
