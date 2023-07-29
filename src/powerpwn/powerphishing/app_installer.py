import json
import logging
import os
from time import sleep
from typing import Any, Dict

from requests import Response

from powerpwn.cli.const import LOGGER_NAME
from powerpwn.powerdump.utils.requests_wrapper import init_session

logger = logging.getLogger(LOGGER_NAME)


class AppInstaller:
    def __init__(self, token: str) -> None:
        self.__session = init_session(token)

    def install_app(self, path_to_zip_file: str) -> None:
        # TODO: environment to install, app name, connections, etc
        _, file_name = os.path.split(path_to_zip_file)

        self.__session.headers.update({"Accept-Encoding": "gzip, deflate, br", "accept": "application/json, text/plain, */*"})
        # prepare storage
        logger.info("Preparing app storage")
        res = self.__session.post(
            "https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/environments/Default-fc993b0f-345b-4d01-9f67-9ac4a140dd43/generateResourceStorage?api-version=2016-11-01"
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
        file_name_without_extension = file_name.split(".")[0]
        with open(path_to_zip_file, "rb") as fileobj:
            res = self.__session.put(compose_block_id_url, files={file_name_without_extension: fileobj})
        if res.status_code != 201:
            self.__log_error("Could not upload zip file", res)
            return None

        self.__session.headers.pop("X-Ms-Blob-Type")
        self.__session.headers.update({"X-Ms-Blob-Content-Type": "application/octet-stream"})
        block_list_url = zip_files_shared_access + "&comp=blocklist"
        payload = '<?xml version="1.0" encoding="utf-8"?><BlockList><Latest>YmxvY2stMDAwMDAwMDA=</Latest></BlockList>'
        res = self.__session.put(block_list_url, data=payload)

        if res.status_code != 201:
            self.__log_error("Could not put block list", res)
            return None

        self.__session.headers.pop("X-Ms-Blob-Content-Type")
        self.__session.headers.update({"Authorization": auth})
        # Get import parameters to update
        res = self.__session.post(
            "https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/environments/Default-fc993b0f-345b-4d01-9f67-9ac4a140dd43/listImportParameters?api-version=2016-11-01",
            json={"packageLink": {"value": zip_files_shared_access}},
        )

        if res.status_code != 202:
            self.__log_error("Failed to get import parameters", res)
            return None

        list_import_operations_url = res.headers["Location"]

        wait = int(res.headers["Retry-After"])
        sleep(wait)
        res = self.__session.get(list_import_operations_url)

        # bug: we get 400 with message : ZipFileRejected, try to export later
        if res.status_code != 202:
            self.__log_error("Failed to get import operations", res)
            return None

        res_json = json.loads(res.text)
        if "resources" not in res_json["properties"]:
            logger.error("No resources in import package")
            return None

        props = self.__set_import_params(res_json["properties"])

        # TODO: here to update connections etc
        # Validate import package
        logger.info("Validating import package")
        res = self.__session.post(
            "https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/environments/Default-fc993b0f-345b-4d01-9f67-9ac4a140dd43/validateImportPackage?api-version=2016-11-01",
            json=props,
        )

        if res.status_code != 200:
            self.__log_error("Failed to validate import package", res)
            return None

        # import package
        validation_response = json.loads(res.text)
        res = self.__session.post(
            "https://api.bap.microsoft.com/providers/Microsoft.BusinessAppPlatform/environments/Default-fc993b0f-345b-4d01-9f67-9ac4a140dd43/importPackage?api-version=2016-11-01",
            json=validation_response,
        )

        if res.status_code != 202:
            self.__log_error("Failed to import package", res)
            return None

        redirect = res.headers["Location"]

        sleep(30)

        # verify import is complete
        res = self.__session.get(redirect)
        if res.status_code != 200:
            self.__log_error("Failed to get import status", res)
            return None

        res_json = json.loads(res.text)
        import_status = res_json["properties"]["status"]
        if import_status == "Succeeded":
            logger.info("Import succeeded")
        else:
            logger.error(f"Import failed with status code: {import_status}")

    def share_app_with_org(self, app_id: str, environment_id: str, tenant_id: str) -> None:
        url = f"https://api.powerapps.com/providers/Microsoft.PowerApps/apps/{app_id}/modifyPermissions"
        params = {"api-version": "2020-06-01", "$filter": f"environment eq '{environment_id}'"}
        body = {"put": [{"properties": {"principal": {"email": "", "tenantId": tenant_id, "id": None, "type": "Tenant"}, "roleName": "CanView"}}]}

        res = self.__session.post(url, params=params, json=body)

        if res.status_code != 200:
            self.__log_error("Failed to share app with organization", res)
            return None
        logger.info("App shared with organization")

    def __log_error(self, message: str, res: Response) -> None:
        logger.error(f"{message}. Status code: {res.status_code}, response: {res.text}")

    def __set_import_params(self, input: Dict[str, Any]) -> Dict[str, Any]:
        input["details"]["displayName"] = "my app"
        resources = input["resources"]
        for resource in resources:
            if resource["type"] == "Microsoft.PowerApps/apps":
                resource["selectedCreationType"] = "New"

        return input
