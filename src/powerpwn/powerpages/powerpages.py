import requests
import xmltodict


class PowerPages:
    """
    A class that is responsible for the Power Pages scan
    """

    def __init__(self, args):
        self.args = args
        url = self.normalize_url(args.url)
        self.url = url
        self.scan()

    def normalize_url(self, url):
        if not url.startswith("https://"):
            url = "https://" + url
        if url.endswith("/"):
            url = url[:-1]
        url = url.replace("www.", "")
        return url

    def scan(self):
        url = self.url
        print(f"Checking `{url}`")
        try:
            odata_tables, api_tables = self.get_odata_tables()
            if len(odata_tables) == 0:
                print("You are safe!")
            else:
                print(f"Found {len(odata_tables)} open tables in '{url}'.")
                if len(api_tables):
                    print(f"Examining additional {len(api_tables)} potential tables through the api")
                print("\nChecking each table:")
            for table in odata_tables:
                try:
                    self.get_odata_table_data(table)
                except Exception as e:
                    print(f"Can't access table {table['name']} through the odata right now")
            for table in api_tables:
                try:
                    self.get_api_table_data(table)
                except Exception as e:
                    print(f"Can't access table {table['name']} through the api right now")
        except Exception as e:
            print(f"Can't access `{url}` anonymously")

    def get_odata_tables(self):
        url = self.url
        odata_url = f"{url}/_odata/$metadata"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"}
        resp = requests.get(odata_url, headers=headers)
        odata_tables = []
        api_tables = []
        if 200 <= resp.status_code <= 299:
            content_xml = resp.content.decode("utf-8")
            resp_json = xmltodict.parse(content_xml)
            entity_types = resp_json.get("edmx:Edmx", {}).get("edmx:DataServices", {}).get("Schema", {}).get("EntityType", [])
            entity_sets = (
                resp_json.get("edmx:Edmx", {}).get("edmx:DataServices", {}).get("Schema", {}).get("EntityContainer", {}).get("EntitySet", [])
            )
            table_names = {entity_set["@EntityType"][4:]: entity_set["@Name"] for entity_set in entity_sets}

            for entity in entity_types:
                name = table_names.get(entity.get("@Name", "unknown"), "unknown")
                key = entity.get("Key", {}).get("PropertyRef", {}).get("@Name", "unknown")
                columns = [prop.get("@Name", "unknown") for prop in entity.get("Property", [])]
                odata_tables.append({"name": name, "key": key, "columns": columns})
                if name.endswith("Set"):
                    api_table_name = name.lower()[:-3] + "s"
                    api_tables.append({"name": api_table_name, "key": key, "columns": columns})

        return odata_tables, api_tables

    def get_api_table_data(self, table):
        url = self.url
        table_name = table["name"]
        table_columns = table["columns"]
        api_table_url = f"{url}/_api/{table_name}?$top=1"
        # print()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"}
        resp = requests.get(api_table_url, headers=headers, timeout=5)
        if 200 <= resp.status_code <= 299:
            resp_json = resp.json()
            if len(resp_json["value"]) > 0:
                print(f"Table {table_name} is exposed with all columns through the API!")
                return len(table_columns)
            else:
                print(f"Table {table_name} is accessible but returned no data through the API!")
                return 0
        elif resp.status_code in [400, 403]:
            try:
                resp_json = resp.json()
                error_code = resp_json.get("error", {}).get("code", "")
                if not error_code == "90040101":
                    raise Exception("Unknown error code")
            except Exception as e:
                print(f"Table {table_name} data is safe through the API")
                return
            print(f"Table {table_name} data is not exposed as a whole, checking each column...")
            exposed = []
            for column in table_columns:
                api_column_url = f"{url}/_api/{table_name}?select={column}&$top=1"
                resp = requests.get(api_column_url, headers=headers)
                if 200 <= resp.status_code <= 299:
                    resp_json = resp.json()
                    if len(resp_json["value"]) > 0:
                        exposed.append(column)
            if len(exposed):
                print(f"Table {table_name} has the following columns exposed: {', '.join(exposed)} through the API")
                return len(exposed)
            else:
                print(f"Table {table_name} data is safe through the API")
                return 0

    def get_odata_table_data(self, table):
        url = self.url
        table_name = table["name"]
        table_columns = table["columns"]
        table_url = f"{url}/_odata/{table_name}?$top=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"}
        resp = requests.get(table_url, headers=headers, timeout=10)
        if 200 <= resp.status_code <= 299:
            resp_json = resp.json()
            if len(resp_json["value"]) > 0:
                print(f"Table {table_name} is exposed with all columns through the odata!")
                return len(table_columns)
            else:
                print(f"Table {table_name} is accessible but returned no data through the odata!")
                return 0
        elif resp.status_code in [400, 403]:
            try:
                resp_json = resp.json()
                error_code = resp_json.get("error", {}).get("code", "")
                if not error_code == "90040101":
                    raise Exception("Unknown error code")
            except Exception as e:
                print(f"Table {table_name} data is safe through the odata")
                return
            print(f"Table {table_name} data is not exposed as a whole, checking each column...")
            exposed = []
            for column in table_columns:
                column_url = f"{url}/_odata/{table_name}?select={column}&$top=1"
                resp = requests.get(column_url, headers=headers)
                if 200 <= resp.status_code <= 299:
                    resp_json = resp.json()
                    if len(resp_json["value"]) > 0:
                        exposed.append(column)
            if len(exposed):
                print(f"Table {table_name} has the following columns exposed: {', '.join(exposed)} through the odata")
                return len(exposed)
            else:
                print(f"Table {table_name} data is safe through the odata")
                return 0
