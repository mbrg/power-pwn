import json
import os
import pathlib
from typing import Dict, Generator, List, Optional, Tuple

from powerpwn.powerdump.collect.models.canvas_app_entity import CanvasApp
from powerpwn.powerdump.collect.models.connection_entity import Connection
from powerpwn.powerdump.collect.models.connector_entity import Connector
from powerpwn.powerdump.collect.models.resource_entity_base import ResourceEntityBase
from powerpwn.powerdump.collect.resources_collectors.enums.resource_type import ResourceType
from powerpwn.powerdump.utils.path_utils import entities_path, env_entity_type_path


def load_resources(cache_path: str, env_id: Optional[str] = None) -> Generator[ResourceEntityBase, None, None]:
    yield from load_connections(cache_path, env_id)
    yield from load_canvasapps(cache_path, env_id)
    yield from load_connectors(cache_path, env_id)


def load_connections(cache_path: str, env_id: Optional[str] = None, with_logic_flows: bool = True) -> Generator[Connection, None, None]:
    cache = pathlib.Path(entities_path(cache_path))
    if env_id:
        connections = cache.glob(f"{env_id}/{ResourceType.connection}/*.json")
    else:
        connections = cache.glob(f"*/{ResourceType.connection}/*.json")
    for connection in connections:
        connection_path = "/".join(list(connection.parts))
        with open(connection_path, "r") as fp:
            raw_connection = json.load(fp)
            parsed_connection = Connection.parse_obj(raw_connection)
            if parsed_connection.connector_id == "shared_logicflows" and not with_logic_flows:
                continue
            yield parsed_connection


def load_logic_flows(cache_path: str, env_id: Optional[str] = None) -> Generator[Connection, None, None]:
    cache = pathlib.Path(entities_path(cache_path))
    if env_id:
        connections = cache.glob(f"{env_id}/{ResourceType.connection}/*.json")
    else:
        connections = cache.glob(f"*/{ResourceType.connection}/*.json")
    for connection in connections:
        connection_path = "/".join(list(connection.parts))
        with open(connection_path, "r") as fp:
            raw_connection = json.load(fp)
            parsed_connection = Connection.parse_obj(raw_connection)
            if not parsed_connection.connector_id == "shared_logicflows":
                continue
            yield parsed_connection


def load_canvasapps(cache_path: str, env_id: Optional[str] = None) -> Generator[CanvasApp, None, None]:
    cache = pathlib.Path(entities_path(cache_path))
    if env_id:
        apps = cache.glob(f"{env_id}/{ResourceType.canvas_app}/*.json")
    else:
        apps = cache.glob(f"*/{ResourceType.canvas_app}/*.json")
    for app in apps:
        canvasapps_path = "/".join(list(app.parts))
        with open(canvasapps_path, "r") as fp:
            raw_app = json.load(fp)
            parsed_app = CanvasApp.parse_obj(raw_app)
            yield parsed_app


def get_canvasapp(cache_path: str, env_id: str, app_id: str) -> CanvasApp:
    canvas_apps_in_env_path = env_entity_type_path(env_id, ResourceType.canvas_app, cache_path)
    app_path = pathlib.Path(f"{canvas_apps_in_env_path}/{app_id}.json")
    with open(app_path, "r") as fp:
        raw_app = json.load(fp)
        return CanvasApp.parse_obj(raw_app)


def get_connection(cache_path: str, env_id: str, connection_id: str) -> Connection:
    canvas_apps_in_env_path = env_entity_type_path(env_id, ResourceType.connection, cache_path)
    app_path = pathlib.Path(f"{canvas_apps_in_env_path}/{connection_id}.json")
    with open(app_path, "r") as fp:
        raw_app = json.load(fp)
        return Connection.parse_obj(raw_app)


def get_connector(cache_path: str, env_id: str, api_name: str) -> Connector:
    connectors_path = env_entity_type_path(env_id, ResourceType.connector, cache_path)
    with open(os.path.join(connectors_path, api_name + ".json")) as fp:
        spec = Connector.parse_obj(json.load(fp))
        return spec


def load_connectors(cache_path: str, env_id: Optional[str] = None) -> Generator[Connector, None, None]:
    cache = pathlib.Path(entities_path(cache_path))
    if env_id:
        connectors = cache.glob(f"{env_id}/{ResourceType.connector}/*.json")
    else:
        connectors = cache.glob(f"*/{ResourceType.connector}/*.json")

    for connector in connectors:
        connector_file = "/".join(list(connector.parts))
        with open(connector_file, "r") as fp:
            raw_spec = json.load(fp)
            parsed_spec = Connector.parse_obj(raw_spec)
            yield parsed_spec


def get_environment_ids(cache_path: str) -> List[str]:
    return os.listdir(entities_path(cache_path))


def map_connection_id_to_connector_id_and_env_id(connections: Generator[Connection, None, None]) -> Dict[str, Tuple[str, str]]:
    connection_id_to_connector_id_and_env_id: Dict[str, Tuple[str, str]] = dict()
    for connection in connections:
        connection_id_to_connector_id_and_env_id[connection.connection_id] = connection_id_to_connector_id_and_env_id.get(
            connection.connection_id, (connection.connector_id, connection.environment_id)
        )

    return connection_id_to_connector_id_and_env_id


def map_connector_id_and_env_id_to_connection_ids(connections: Generator[Connection, None, None]) -> Dict[Tuple[str, str], List[str]]:
    connector_id_and_env_id_to_connection_ids: Dict[Tuple[str, str], List[str]] = dict()
    for connection in connections:
        if connection.environment_id.startswith("default"):
            connection.environment_id = connection.environment_id.replace("default", "Default")
        connector_id_and_env_id_to_connection_ids[
            (connection.connector_id, connection.environment_id)
        ] = connector_id_and_env_id_to_connection_ids.get((connection.connector_id, connection.environment_id), []) + [connection.connection_id]

    return connector_id_and_env_id_to_connection_ids
