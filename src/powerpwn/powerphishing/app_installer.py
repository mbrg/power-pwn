import json
import logging
import os
from time import sleep
from typing import Any, Dict, Union

from requests import Response

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.powerdump.utils.requests_wrapper import init_session

logger = logging.getLogger(LOGGER_NAME)


class AppInstaller:
    def __init__(self, token: str) -> None:
        self.__session = init_session(token)

    def install_app(self, path_to_zip_file: str, app_display_name: str, env_id: str) -> None:
        if not os.path.exists(path_to_zip_file):
            logger.error(f"Could not find file: {path_to_zip_file}")
            return None

        _, file_name = os.path.split(path_to_zip_file)

        self.__session.headers.update({"Accept-Encoding": "gzip, deflate, br", "accept": "application/json, text/plain, */*"})
        # prepare storage
        logger.info("Preparing app storage")
        res = self.__session.post(
            f"https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/environments/{env_id}/generateResourceStorage?api-version=2016-11-01"
        )
        if res.status_code != 200:
            self.__log_error("Could not generate app storage", res)
            return None

        # upload zip file
        logger.info("Uploading zip file")
        shared_access_sig = json.loads(res.text)["sharedAccessSignature"]
        self.__session.headers.update({"X-Ms-Blob-Type": "BlockBlob"})
        auth = self.__session.headers.pop("Authorization")

        shared_access_splitted = shared_access_sig.split("?")
        zip_files_shared_access = shared_access_splitted[0] + f"/{file_name}?" + shared_access_splitted[1]
        compose_block_id_url = zip_files_shared_access + "&comp=block&blockid=YmxvY2stMDAwMDAwMDA="

        with open(path_to_zip_file, "rb") as fileobj:
            res = self.__session.put(compose_block_id_url, data=fileobj)
        if res.status_code != 201:
            self.__log_error("Could not upload zip file", res)
            return None

        logger.info("Application zip file uploaded successfully")

        self.__session.headers.pop("X-Ms-Blob-Type")
        self.__session.headers.update({"X-Ms-Blob-Content-Type": "application/octet-stream"})
        block_list_url = zip_files_shared_access + "&comp=blocklist"
        payload = '<?xml version="1.0" encoding="utf-8"?><BlockList><Latest>YmxvY2stMDAwMDAwMDA=</Latest></BlockList>'
        res = self.__session.put(block_list_url, data=payload)

        if res.status_code != 201:
            self.__log_error("Could not put block list", res)
            return None

        self.__session.headers.pop("X-Ms-Blob-Content-Type")

        logger.info("Getting import parameters...")
        self.__session.headers.update({"Authorization": auth})
        # Get import parameters to update
        res = self.__session.post(
            f"https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/environments/{env_id}/listImportParameters?api-version=2016-11-01",
            json={"packageLink": {"value": zip_files_shared_access}},
        )

        if res.status_code != 202:
            self.__log_error("Failed to get import parameters", res)
            return None

        list_import_operations_url = res.headers["Location"]

        wait = int(res.headers["Retry-After"])
        sleep(wait)

        logger.info("Listing import parameters operations...")
        res = self.__session.get(list_import_operations_url)

        if res.status_code != 200:
            self.__log_error("Failed to get import operations", res)
            return None

        res_json = json.loads(res.text)
        if "resources" not in res_json["properties"]:
            logger.error("No resources in import package")
            return None

        logger.info("Setting import parameters...")
        props = self.__set_import_params(res_json["properties"], app_display_name)

        # TODO: here to update connections etc
        # Validate import package
        logger.info("Validating import package...")
        res = self.__session.post(
            f"https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/environments/{env_id}/validateImportPackage?api-version=2016-11-01",
            json=props,
        )

        if res.status_code != 200:
            self.__log_error("Failed to validate import package", res)
            return None

        # import package
        logger.info("Importing package...")
        validation_response = json.loads(res.text)
        res = self.__session.post(
            f"https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/environments/{env_id}/importPackage?api-version=2016-11-01",
            json=validation_response,
        )

        if res.status_code != 202:
            self.__log_error("Failed to import package", res)
            return None

        redirect = res.headers["Location"]

        sleep(10)

        # verify import is complete
        logger.info("Verifying import status...")
        res = self.__session.get(redirect)
        if res.status_code not in (200, 202):
            self.__log_error("Failed to get import status", res)
            return None

        res_json = json.loads(res.text)
        import_status = res_json["properties"]["status"]
        if import_status == "Succeeded":
            app_id = self.__set_get_app_id(res_json["properties"]["resources"])
            self.__log_app_details(app_id, env_id)
            self.__publish_app(app_id)
        else:
            message = res_json["properties"]["errors"][0]["message"]
            logger.error(f"Import failed. Reason: {message}")

    def share_app_with_org(self, app_id: str, environment_id: str, tenant_id: str) -> None:
        url = f"https://api.powerapps.com/providers/Microsoft.PowerApps/apps/{app_id}/modifyPermissions"
        params = {"api-version": "2020-06-01", "$filter": f"environment eq '{environment_id}'"}
        body = {"put": [{"properties": {"principal": {"email": "", "tenantId": tenant_id, "id": None, "type": "Tenant"}, "roleName": "CanView"}}]}

        res = self.__session.post(url, params=params, json=body)

        if res.status_code != 200:
            self.__log_error("Failed to share app with organization", res)
            return None
        logger.info("App shared with organization")

    def __publish_app(self, app_id: str) -> None:
        logger.info("Publishing app...")
        url = f"https://api.powerapps.com/providers/Microsoft.PowerApps/apps/{app_id}/publish"
        params = {"api-version": "2020-06-01"}
        res = self.__session.post(url, params=params)
        if res.status_code != 200:
            self.__log_error("Failed to publish app", res)
        else:
            logger.info("App published")

    def __log_error(self, message: str, res: Response) -> None:
        logger.error(f"{message}. Status code: {res.status_code}, response: {res.text}")

    def __set_import_params(self, input: Dict[str, Any], app_display_name: str) -> Dict[str, Any]:
        resources = input["resources"]
        for _, resource in resources.items():
            if resource["type"] == "Microsoft.PowerApps/apps":
                resource["selectedCreationType"] = "New"
                resource["details"]["displayName"] = app_display_name

        return input

    def __log_app_details(self, app_id: str, env_id: str) -> None:
        app_web_url = f"https://make.powerapps.com/environments/{env_id}/apps/{app_id}/details"

        logger.info(f"Application installed with id {app_id}.")
        logger.info(f"Application web url: {app_web_url}")
        logger.info("Getting app run url...")
        if app := self.__get_canvasapp(app_id, env_id):
            logger.info(f"Application run url : {app['properties']['appPlayUri']}")
        else:
            logger.error("Failed to get app run url")

    def __set_get_app_id(self, resources: Dict[str, Any]) -> str:
        for _, resource in resources.items():
            if resource["type"] == "Microsoft.PowerApps/apps":
                return resource["name"]
        return ""

    def __get_canvasapp(self, app_id: str, env_id: str) -> Union[Dict[str, Any], None]:
        url = f"https://api.powerapps.com/providers/Microsoft.PowerApps/apps/{app_id}"
        params = {"api-version": "2016-11-01", "$filter": f"environment eq '{env_id}'"}
        self.__session.headers.pop("Accept-Encoding")
        res = self.__session.get(url=url, params=params)
        if res.status_code == 200:
            return json.loads(res.text)
        return None
