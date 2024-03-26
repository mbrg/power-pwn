import json
from typing import Optional

from flask import Flask, render_template
from swagger_ui import flask_api_doc

from powerpwn.cli.const import TOOL_NAME
from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase
from powerpwn.powerdump.utils.model_loaders import (
    get_canvasapp,
    get_connection,
    get_connector,
    load_canvasapps,
    load_connections,
    load_connectors,
    load_logic_flows,
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


def env_resources_table_wrapper(cache_path: str):
    def env_resources_table(env_id: str):
        resources = list(load_resources(cache_path=cache_path, env_id=env_id))
        title = f"{TOOL_NAME} - environment {env_id}"
        return render_template("resources_table.html", title=title, resources=resources)

    return env_resources_table


def env_resources_table_by_resource_type_wrapper(cache_path: str):
    def env_per_resource_type_table(env_id: str, resource_type: str):
        if resource_type == "app":
            resources = load_canvasapps(cache_path, env_id)
        elif resource_type == "credentials":
            resources = load_connections(cache_path, env_id, with_logic_flows=False)
        elif resource_type == "automation":
            resources = load_logic_flows(cache_path, env_id)
        elif resource_type == "connector":
            resources = load_connectors(cache_path, env_id)
        title = f"{TOOL_NAME} - environment {env_id} - {resource_type}"

        return render_template("resources_table.html", title=title, resources=resources)

    return env_per_resource_type_table


def full_connection_table_wrapper(cache_path: str):
    def full_connection_table():
        connections = list(load_connections(cache_path=cache_path, with_logic_flows=False))

        return render_template("connections_table.html", title=f"{TOOL_NAME} - Credentials", resources=connections)

    return full_connection_table


def full_logic_flows_table_wrapper(cache_path: str):
    def full_logic_flows_table():
        connections = list(load_logic_flows(cache_path=cache_path))

        return render_template("logic_flows_table.html", title=f"{TOOL_NAME} - Automations", resources=connections)

    return full_logic_flows_table


def flt_connection_table_wrapper(cache_path: str):
    def flt_connection_table(connector_id: str):
        connections = [conn for conn in load_connections(cache_path=cache_path) if conn.connector_id == connector_id]

        return render_template("connections_table.html", title=f"{TOOL_NAME} - {connector_id}", resources=connections)

    return flt_connection_table


def full_canvasapps_table_wrapper(cache_path: str):
    def full_canvasapp_table():
        apps = list(load_canvasapps(cache_path=cache_path))

        return render_template("canvasapps_table.html", title=f"{TOOL_NAME} - Applications", resources=apps)

    return full_canvasapp_table


def full_connectors_table_wrapper(cache_path: str):
    def full_connector_table():
        connectors = list(load_connectors(cache_path=cache_path))

        return render_template("connectors_table.html", title=f"{TOOL_NAME} - Connectors", resources=connectors)

    return full_connector_table


def flt_resource_wrapper(cache_path: str):
    def get_resource_page(resource_type: str, env_id: str, resource_id: str):
        resource: Optional[ResourceEntityBase] = None
        if resource_type in ("app", "canvas_app"):
            resource = get_canvasapp(cache_path, env_id, resource_id)
        elif resource_type in ("credentials", "automation", "connection"):
            resource = get_connection(cache_path, env_id, resource_id)
        elif resource_type == "connector":
            resource = get_connector(cache_path, env_id, resource_id)

        if resource:
            return render_template(
                "json_object.html", title=f"{TOOL_NAME} - {resource_type} {resource_id}", json_object=json.dumps(resource.raw_json)
            )

    return get_resource_page
