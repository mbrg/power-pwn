import base64
import io
import os
from typing import List

import PIL.Image as Image
import requests

from powerpwn.powerdump.collect.data_collectors.connections_data_collectors.connectors import API_NAME_TO_CONNECTOR_CLS
from powerpwn.powerdump.collect.data_collectors.enums.data_dump_source import DataDumpSource
from powerpwn.powerdump.collect.data_collectors.idata_collector import IDataCollector
from powerpwn.powerdump.collect.models.data_dump_entity import DataDumpWithContext
from powerpwn.powerdump.collect.models.data_store_entity import DataStoreWithContext
from powerpwn.powerdump.utils.model_loaders import get_connector, load_connections


class ConnectionsDataCollector(IDataCollector):
    def __init__(self, cache_path: str) -> None:
        self.__cache_path = cache_path

    def collect(self, session: requests.Session, env_id: str, output_dir_path: str) -> None:
        data_dumps: List[DataDumpWithContext] = []
        connections_dumps_root_dir = os.path.join(output_dir_path, DataDumpSource.connections.value)

        for connection in load_connections(cache_path=self.__cache_path, env_id=env_id):
            current_data_stores: List[DataStoreWithContext] = []
            connection_id = connection.connection_id
            api_name = connection.api_name

            connections_apis_dir = os.path.join(connections_dumps_root_dir, connection.api_name)

            if api_name in API_NAME_TO_CONNECTOR_CLS:
                connection_dump_root_dir = os.path.join(connections_apis_dir, connection.connection_id)

                connector_cls = API_NAME_TO_CONNECTOR_CLS[api_name]
                spec = get_connector(self.__cache_path, connection.environment_id, connector_cls.api_name())

                connector_cls_instance = connector_cls(session=session, spec=spec, connection_id=connection_id)
                current_data_stores = connector_cls_instance.ping(connection_parameters=connection.connection_parameters)

                for data_store in current_data_stores:
                    data_records = connector_cls_instance.enum(data_store=data_store)
                    for data_record in data_records:
                        data_dump_type_dir = os.path.join(connection_dump_root_dir, data_record.data_record.record_type)
                        os.makedirs(data_dump_type_dir, exist_ok=True)
                        data_dump = connector_cls_instance.dump(data_record=data_record)
                        data_dump_path = os.path.join(data_dump_type_dir, f"{data_record.data_record.record_name}.{data_dump.data_dump.extension}")
                        encoding = data_dump.data_dump.encoding
                        extension = data_dump.data_dump.extension
                        content = data_dump.data_dump.content
                        if extension == "png":
                            self.__dump_png(content, data_dump_path)
                        else:
                            with open(data_dump_path, "w") as f:
                                content = content.decode(encoding) if encoding else content
                                f.write(content)
                        data_dumps.append(data_dump)

    def __dump_png(self, bytes: bytes, path: str) -> None:
        image_bytes = base64.b64decode(bytes)
        img = Image.open(io.BytesIO(image_bytes))
        img.save(path)
