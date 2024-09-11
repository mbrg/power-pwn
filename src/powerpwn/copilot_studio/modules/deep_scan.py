import logging
import os
import re
import signal
import subprocess  # nosec
from datetime import datetime

import pandas as pd
import requests
import xlsxwriter

from powerpwn.copilot_studio.modules.path_utils import get_project_file_path


def sort_unique_values_in_file(file_path):
    try:
        # Read the content of the file
        with open(file_path, "r") as file:
            content = file.read()

        # Split the content into individual values (assuming each value is on a new line)
        values = content.splitlines()

        # Remove duplicates by converting the list to a set
        unique_values = set(values)

        # Sort the unique values
        sorted_unique_values = sorted(unique_values)

        # Write the sorted unique values back to the file
        with open(file_path, "w") as file:
            for value in sorted_unique_values:
                file.write(value + "\n")

        print(f"File '{file_path}' has been updated with sorted unique values.")

        return sorted_unique_values
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


# Function to transform the URL
def transform_url(url):
    pattern = re.compile(
        r"https://default([a-z0-9]+)\.([a-z0-9]+)\.environment\.api\.powerplatform\.com/powervirtualagents/botsbyschema/([^/]+)/canvassettings\?api-version=2022-03-01-preview"
    )
    match = pattern.match(url)
    if match:
        env_part = match.group(1)
        additional_part = match.group(2)
        formatted_env_part = f"{env_part[:8]}-{env_part[8:12]}-{env_part[12:16]}-{env_part[16:20]}-{env_part[20:24]}{env_part[24:]}{additional_part}"
        bot_part = match.group(3)
        transformed_url = f"https://copilotstudio.microsoft.com/environments/Default-{formatted_env_part}/bots/{bot_part}/canvas\\?__version__\\=2"
        return transformed_url
    return url


def check_and_append(file_path, value):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()

        # Remove any trailing newline characters
        lines = [line.strip() for line in lines]

        if value not in lines:
            with open(file_path, "a") as file:
                file.write(f"{value}\n")
            print(f"New tenant, '{value}' has been added to the file.")
            return True
        else:
            print(f"'{value}' is already in the file. Skipping.")
            return False

    except FileNotFoundError:
        with open(file_path, "w") as file:
            file.write(f"{value}\n")
        print(f"File not found. Tenant '{value}' has been added to a new file.")
        return True


def get_tenant_id(domain: str, timeout: int = 10):
    """
    Retrieve the Azure AD tenant ID for a given domain.

    :param domain: The domain to query.
    :param timeout: The timeout (in seconds) for the HTTP request.
    :return: The tenant ID or None if not found.
    """
    print("Domain: ", domain)
    url = f"https://login.microsoftonline.com/{domain}/v2.0/.well-known/openid-configuration"
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            tenant_id = response.json().get("issuer").split("/")[3]
            return tenant_id
        else:
            logging.error(f"Failed to retrieve tenant ID: {response.status_code} {response.text}")
            return None
    except requests.Timeout:
        logging.error(f"Request timed out after {timeout} seconds")
        return None
    except requests.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return None


def get_ffuf_results(
    endpoint: str,
    wordlist_prefix: str,
    wordlist_suffix_1: str,
    wordlist_suffix_2: str,
    wordlist_suffix_3: str,
    rate_limit: int,
    threads: int,
    domain: str,
    ffuf_flag: str,
    timeout: int,
) -> str:
    """
    Run FFUF on the input endpoint:
      1. Use fuzzing locations in the URL based on the FUZZ1/2/3 keywords.
      2. Used the prepared wordlists.
      3. Use rate limiting and threads according to the input parameters.

    :param endpoint: The endpoint to fuzz (the MSFT API we retrieved using the environment ID to check for the existance of the CoPilot demo website using the botsBySchema API
    :param wordlist_prefix: The wordlist to use to fuzz the solution prefix (included in the bot demo website name)
    :param wordlist_suffix_1: The wordlist to use to fuzz the bot name
    :param wordlist_suffix_2: The wordlist to use to fuzz the suffix of the bot name (e.g., 1 in copilot1
    :param wordlist_suffix_3: The wordlist to use to fuzz the suffix of the bot name (e.g., Test in copilot1Test
    :param rate_limit: Request per second to use
    :param threads: Threads to use
    :param domain: The domain to be scanned
    :param ffuf_flag: The FFUF flag to use (silent/verbose)
    :param timeout: The timeout (in seconds) to set for each one of the FFUF scans (1-word/2-word/3-word)
    :return: Returns the FFUF terminal output per line, to allow users to see progress (-s can be used to silence this)
    """
    ffuf_path_1 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{domain}_one_word_names.csv")

    # Run first for one-letter words
    command = [
        "ffuf",
        ffuf_flag,
        "-w",
        f"{get_project_file_path('helpers', wordlist_prefix)}:FUZZ1",
        "-w",
        f"{get_project_file_path('helpers', wordlist_suffix_1)}:FUZZ2",
        "-u",
        f"{endpoint}FUZZ1_FUZZ2/canvassettings?api-version=2022-03-01-preview",
        "-fr",
        '"demoWebsiteErrorCode": "404"',
        "-ac",
        "-rate",
        str(rate_limit),
        "-t",
        str(threads),
        "-se",
        "-maxtime-job",
        str(timeout),
        "-of",
        "csv",
        "-o",
        f"{ffuf_path_1}",
        "-H",
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "-H",
        "Accept: application/json, text/plain, */*",
        "-H",
        "Accept-Language: en-US,en;q=0.5",
        "-H",
        "Accept-Encoding: gzip, deflate, br, zstd",
        "-H",
        "Origin: https://copilotstudio.microsoft.com",
        "-H",
        "DNT: 1",
        "-H",
        "Connection: keep-alive",
        "-H",
        "Sec-Fetch-Dest: empty",
        "-H",
        "Sec-Fetch-Mode: cors",
        "-H",
        "Sec-Fetch-Site: cross-site",
        "-H",
        "Sec-GPC: 1",
        "-H",
        "Via: 1.1 103.230.38.175",
        "-H",
        "TE: trailers",
    ]

    print("\nScanning for 1-word bot names")

    # TODO: Verify and improve guardrails for using subprocess
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)  # nosec
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line, popen
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)

    ffuf_path_2 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{domain}_two_word_names.csv")

    # Run for 2-letter words
    command = [
        "ffuf",
        ffuf_flag,
        "-w",
        f"{get_project_file_path('helpers', wordlist_prefix)}:FUZZ1",
        "-w",
        f"{get_project_file_path('helpers', wordlist_suffix_1)}:FUZZ2",
        "-w",
        f"{get_project_file_path('helpers', wordlist_suffix_2)}:FUZZ3",
        "-u",
        f"{endpoint}FUZZ1_FUZZ2FUZZ3/canvassettings?api-version=2022-03-01-preview",
        "-fr",
        '"demoWebsiteErrorCode": "404"',
        "-ac",
        "-rate",
        str(rate_limit),
        "-t",
        str(threads),
        "-se",
        "-maxtime-job",
        str(timeout),
        "-of",
        "csv",
        "-o",
        f"{ffuf_path_2}",
        "-H",
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "-H",
        "Accept: application/json, text/plain, */*",
        "-H",
        "Accept-Language: en-US,en;q=0.5",
        "-H",
        "Accept-Encoding: gzip, deflate, br, zstd",
        "-H",
        "Origin: https://copilotstudio.microsoft.com",
        "-H",
        "DNT: 1",
        "-H",
        "Connection: keep-alive",
        "-H",
        "Sec-Fetch-Dest: empty",
        "-H",
        "Sec-Fetch-Mode: cors",
        "-H",
        "Sec-Fetch-Site: cross-site",
        "-H",
        "Sec-GPC: 1",
        "-H",
        "Via: 1.1 103.230.38.175",
        "-H",
        "TE: trailers",
    ]

    print("\nScanning for 2-word bot names")

    # TODO: Verify and improve guardrails for using subprocess
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)  # nosec
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line, popen
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)

    ffuf_path_3 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{domain}.csv")

    # Use for 3-letter words
    command = [
        "ffuf",
        ffuf_flag,
        "-w",
        f"{get_project_file_path('helpers', wordlist_prefix)}:FUZZ1",
        "-w",
        f"{get_project_file_path('helpers', wordlist_suffix_1)}:FUZZ2",
        "-w",
        f"{get_project_file_path('helpers', wordlist_suffix_2)}:FUZZ3",
        "-w",
        f"{get_project_file_path('helpers', wordlist_suffix_3)}:FUZZ4",
        "-u",
        f"{endpoint}FUZZ1_FUZZ2FUZZ3FUZZ4/canvassettings?api-version=2022-03-01-preview",
        "-fr",
        '"demoWebsiteErrorCode": "404"',
        "-ac",
        "-rate",
        str(rate_limit),
        "-t",
        str(threads),
        "-se",
        "-maxtime-job",
        str(timeout),
        "-of",
        "csv",
        "-o",
        f"{ffuf_path_3}",
        "-H",
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "-H",
        "Accept: application/json, text/plain, */*",
        "-H",
        "Accept-Language: en-US,en;q=0.5",
        "-H",
        "Accept-Encoding: gzip, deflate, br, zstd",
        "-H",
        "Origin: https://copilotstudio.microsoft.com",
        "-H",
        "DNT: 1",
        "-H",
        "Connection: keep-alive",
        "-H",
        "Sec-Fetch-Dest: empty",
        "-H",
        "Sec-Fetch-Mode: cors",
        "-H",
        "Sec-Fetch-Site: cross-site",
        "-H",
        "Sec-GPC: 1",
        "-H",
        "Via: 1.1 103.230.38.175",
        "-H",
        "TE: trailers",
    ]

    print("\nScanning for 3-word bot names")

    # TODO: Verify and improve guardrails for using subprocess
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)  # nosec
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line, popen
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def get_ffuf_results_prefix(endpoint: str, wordlist_prefix: str, wordlist_suffix_1: str, rate_limit: int, threads: int, timeout: int) -> str:
    """
    Run FFUF on the input endpoint:
      1. Use fuzzing locations in the URL based on the FUZZ1/2/3 keywords.
      2. Used the prepared wordlists.
      3. Use rate limiting and threads according to the input parameters.

    :param endpoint: The endpoint to fuzz (the MSFT API we retrieved using the environment ID to check for the existence of the CoPilot demo website using the botsBySchema API
    :param wordlist_prefix: The wordlist to use to fuzz the solution prefix (included in the bot demo website name)
    :param wordlist_suffix_1: The wordlist to use to fuzz the bot name
    :param rate_limit: Request per second to use
    :param threads: Threads to use
    :param timeout: The timeout (in seconds) to set for each one of the FFUF scans (1-word/2-word/3-word)
    :return: Returns the FFUF terminal output per line, to allow users to see progress (-s can be used to silence this)
    """
    command = [
        "ffuf",
        "-v",  # Prefix scan should be verbose ATM to identify a correct hit
        "-w",
        f"{get_project_file_path('helpers', wordlist_prefix)}:FUZZ1",
        "-w",
        f"{get_project_file_path('helpers', wordlist_suffix_1)}:FUZZ2",
        "-u",
        f"{endpoint}FUZZ1_FUZZ2/canvassettings?api-version=2022-03-01-preview",
        "-fr",
        '"demoWebsiteErrorCode": "404"',
        "-ac",
        "-rate",
        str(rate_limit),
        "-t",
        str(threads),
        "-se",
        "-maxtime-job",
        str(timeout),
        "-H",
        "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "-H",
        "Accept: application/json, text/plain, */*",
        "-H",
        "Accept-Language: en-US,en;q=0.5",
        "-H",
        "Accept-Encoding: gzip, deflate, br, zstd",
        "-H",
        "Origin: https://copilotstudio.microsoft.com",
        "-H",
        "DNT: 1",
        "-H",
        "Connection: keep-alive",
        "-H",
        "Sec-Fetch-Dest: empty",
        "-H",
        "Sec-Fetch-Mode: cors",
        "-H",
        "Sec-Fetch-Site: cross-site",
        "-H",
        "Sec-GPC: 1",
        "-H",
        "Via: 1.1 103.230.38.175",
        "-H",
        "TE: trailers",
    ]

    # TODO: Verify and improve guardrails for using subprocess
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)  # nosec
    for stdout_line in iter(popen.stdout.readline, ""):
        if "FUZZ1:" in stdout_line:
            fuzz1_value = stdout_line.split("FUZZ1:")[1].split()[0]
            popen.send_signal(signal.SIGTERM)  # Send SIGTERM to ask ffuf to terminate gracefully
            yield fuzz1_value, popen
            break
        yield None, popen
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)


def print_brand(tenant: str, timeout: int = 10):
    """
    Retrieve and print the brand for a given tenant ID.
    Using AADInternals, possible TBD directly to MSFT in the future.

    :param tenant: The tenant ID to query.
    :param timeout: The timeout (in seconds) for the HTTP request.
    """
    # URL and headers for the request (using a set of valid request headers)
    url = f"https://aadinternals.azurewebsites.net/api/tenantinfo?tenantId={tenant}"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Origin": "https://aadinternals.com",
        "Referer": "https://aadinternals.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-gpc": "1",
    }

    try:
        # Make the request with a timeout
        response = requests.get(url, headers=headers, timeout=timeout)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            domain = data.get("tenantBrand", None)
            print(f"Brand found for tenant {tenant}: {domain}")
        else:
            print(f"No brand found for tenant {tenant}")
            logging.error(f"Failed to retrieve tenant brand: {response.status_code} {response.text}")

    except requests.Timeout:
        print(f"Request timed out after {timeout} seconds")
        logging.error(f"Request timed out after {timeout} seconds")

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        logging.error(f"An error occurred: {e}")

    # Make the request
    response = requests.get(url, headers=headers, timeout=timeout)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        domain = data.get("tenantBrand", None)
        print(f"Brand found for tenant {tenant}: {domain}")

    else:
        print(f"No brand found for tenant {tenant}")


def run_pup_commands(existing_bots):
    if os.name == "nt":  # Windows
        pup_path = get_project_file_path("tools/pup_is_webchat_live", "is_chat_live_windows.js")
    else:
        pup_path = get_project_file_path("tools/pup_is_webchat_live", "is_chat_live.js")
    # Construct the command to run the Node.js script with xargs
    open_bots_path = get_project_file_path("final_results/", "chat_exists_output.txt")
    # Empty the file
    with open(open_bots_path, "w") as _:
        pass
    for bot_url in existing_bots:
        try:
            # Construct the shell command
            command = f"node {pup_path} {bot_url}"
            logging.debug(f"Running command: {command}")
            # TODO: Verify and improve guardrails for using subprocess + replace shell=True
            # Run the command
            subprocess.run(command, shell=True, check=True)  # nosec
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while running puppeteer: {e}")

    if os.path.exists(open_bots_path):
        return sort_unique_values_in_file(open_bots_path)
    return []


def get_bot_name_from_url(bot_url):
    re_match = re.search(r"/bots/(.*?)/canvas", bot_url)
    if re_match:
        return re_match.group(1)
    return ""


class DeepScan:
    """
    A class that is responsible for the CPS deep scan
    """

    def __init__(self, args):
        self.args = args
        self.default_env_found = False
        self.default_solution_prefix_found = False
        self.existing_bots = []
        self.open_bots = []
        self.run()

    def dump_results(self):
        today_str = datetime.today().date().strftime("%Y_%m_%d")
        if self.args.domain:
            file_name = f"{self.args.domain}_{today_str}.xlsx"
            title = "Domain"
            value = self.args.domain
        elif self.args.tenant_id:
            file_name = f"{self.args.tenant_id}_{today_str}.xlsx"
            title = "Tenant ID"
            value = self.args.tenant_id
        else:
            logging.info("No domain/ tenant supplied, exiting...")
            return

        out_file_path = get_project_file_path("final_results/", file_name)

        workbook = xlsxwriter.Workbook(out_file_path)
        worksheet = workbook.add_worksheet()
        existing_bots = list(set(self.existing_bots))
        open_bots = list(set(self.open_bots))

        data = [
            [title, value],
            ["Tenant default environment found?", "Yes" if self.default_env_found else "No"],
            ["Default Solution Prefix found?", "Yes" if self.default_solution_prefix_found else "No"],
            ["No. of existing bots found", str(len(existing_bots))],
            ["No. of open bots found (don't require auth to interact with)", str(len(open_bots))],
        ]
        if len(existing_bots):
            data.append(["Existing Bots Names"])
            for i in range(len(existing_bots)):
                data[-1].append(get_bot_name_from_url(existing_bots[i]))

        if len(open_bots):
            data.append(["Open Bots Names"])
            for i in range(len(open_bots)):
                data[-1].append(get_bot_name_from_url(open_bots[i]))

        # Adding a table is kinda bugged so this is commented out.
        # worksheet.add_table(0, 0, max(len(x) for x in data), len(data))
        for i in range(len(data)):
            worksheet.write_column(0, i, data[i])

        while True:
            try:
                workbook.close()
            except xlsxwriter.exceptions.FileCreateError as e:
                decision = input(
                    "Exception caught in workbook.close(): %s\n"
                    "Please close the file if it is open in Excel.\n"
                    "Try to write file again? [Y/n]: " % e
                )
                if decision != "n":
                    continue

            break

    def run(self):
        # Determine the ffuf flag based on the provided mode
        ffuf_flag = "-v" if self.args.mode == "verbose" else "-s"

        # TODO: use functions to avoid duplicate code

        if self.args.domain:

            ffuf_path_1 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{self.args.domain}_one_word_names.csv")

            ffuf_path_2 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{self.args.domain}_two_word_names.csv")
            ffuf_path_3 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{self.args.domain}.csv")

            tenant_id = get_tenant_id(self.args.domain)

            if tenant_id:
                self.default_env_found = True
                logging.info(f"Tenant ID: {tenant_id}")
                logging.info(
                    "Use the following URL to access the CoPilotStudio demo website: \n"
                    f"https://copilotstudio.microsoft.com/environments/Default-{tenant_id}/bots/"
                )

                tenant_id_for_api = tenant_id.replace("-", "")
                env_bots_endpoint = f"https://default{tenant_id_for_api[:-2]}.{tenant_id_for_api[-2:]}.environment.api.powerplatform.com/powervirtualagents/botsbyschema/"
                logging.info(f"Endpoint for the default environment bots schema: {env_bots_endpoint}")

                fuzz1_value = None
                fuzz_file_name = f"fuzz1_value_{self.args.domain}.txt"
                fuzz_file_path = get_project_file_path("internal_results/prefix_fuzz_values", f"{fuzz_file_name}")

                print("Checking if an existing solution publisher prefix value exists for this domain.")

                # Check if the file exists
                if os.path.exists(fuzz_file_path):
                    # Open the file and read the first line
                    with open(fuzz_file_path, "r") as file:
                        first_line = file.readline().strip()  # .strip() removes any leading/trailing whitespace

                    print("An existing solution publisher prefix value was found for this domain, continuing to search for CoPilot demo websites.")

                    if first_line:
                        self.default_solution_prefix_found = True
                        for line, popen in get_ffuf_results(
                            env_bots_endpoint,
                            f"{fuzz_file_path}",
                            "botname_1_no_capital.txt",
                            "botname_2_to_3_capital.txt",
                            "botname_2_to_3_capital.txt",
                            self.args.rate,
                            self.args.threads,
                            self.args.domain,
                            ffuf_flag,
                            self.args.timeout_bots,
                        ):
                            print(line, end="")

                        logging.info(
                            f"FFUF executed successfully for the found solution publisher prefix, results saved to internal_results/ffuf_results/ffuf_results_{self.args.domain}.txt"
                        )

                        df1 = pd.DataFrame()
                        df2 = pd.DataFrame()
                        df3 = pd.DataFrame()

                        # Read the CSV file
                        if os.path.exists(ffuf_path_1):
                            df1 = pd.read_csv(ffuf_path_1)

                        if os.path.exists(ffuf_path_2):
                            df2 = pd.read_csv(ffuf_path_2)

                        if os.path.exists(ffuf_path_3):
                            df3 = pd.read_csv(ffuf_path_3)

                        df = pd.concat([df1, df2, df3], ignore_index=True)

                        # Transform the URL column
                        transformed_urls = df["url"].apply(transform_url)

                        url_file = f"url_output_{self.args.domain}.txt"
                        url_file_path = get_project_file_path("internal_results/url_results", f"{url_file}")

                        # Save the result to a new text file
                        with open(f"{url_file_path}", "w") as f:
                            for url in transformed_urls:
                                f.write(f"{url}\n")

                        self.existing_bots = sort_unique_values_in_file(f"{url_file_path}")

                        print(f"\nTransformed URLs saved to {url_file_path}")
                        print("\nChecking accessible CoPilot demo websites")

                        self.open_bots = run_pup_commands(self.existing_bots)

                        print("Done, results saved under final_results/chat_exists_output.txt")

                    else:
                        logging.error("Did not find a solution publisher prefix")
                else:
                    print("No existing solution publisher prefix value found for this domain, starting prefix scan.")

                    for value, popen in get_ffuf_results_prefix(
                        env_bots_endpoint,
                        "prefix_wordlist_char_fix_basic.txt",
                        "suffix_wordlist_basic_1.txt",
                        self.args.rate,
                        self.args.threads,
                        self.args.timeout_prefix,
                    ):
                        if value:
                            fuzz1_value = value
                            print("Found default solution publisher prefix, proceeding to scan bot names")
                            break

                    fuzz_file_name = f"fuzz1_value_{self.args.domain}.txt"
                    fuzz_file_path = get_project_file_path("internal_results/prefix_fuzz_values", f"{fuzz_file_name}")

                    if fuzz1_value:
                        self.default_solution_prefix_found = True
                        with open(fuzz_file_path, "w") as file:
                            file.write(fuzz1_value + "\n")

                        # Continue with further logic using the new FUZZ1 wordlist
                        logging.info(f"Found solution publisher prefix: {fuzz1_value}")
                        logging.info("Running ffuf with new FUZZ1 values")

                        for line, popen in get_ffuf_results(
                            env_bots_endpoint,
                            f"{fuzz_file_path}",
                            "botname_1_no_capital.txt",
                            "botname_2_to_3_capital.txt",
                            "botname_2_to_3_capital.txt",
                            self.args.rate,
                            self.args.threads,
                            self.args.domain,
                            ffuf_flag,
                            self.args.timeout_bots,
                        ):
                            print(line, end="")

                        logging.info(
                            f"FFUF executed successfully for the found solution publisher prefix, results saved to internal_results/ffuf_results/ffuf_results_{self.args.domain}.txt"
                        )

                        df1 = pd.DataFrame()
                        df2 = pd.DataFrame()
                        df3 = pd.DataFrame()

                        # Read the CSV file
                        if os.path.exists(ffuf_path_1):
                            df1 = pd.read_csv(ffuf_path_1)

                        if os.path.exists(ffuf_path_2):
                            df2 = pd.read_csv(ffuf_path_2)

                        if os.path.exists(ffuf_path_3):
                            df3 = pd.read_csv(ffuf_path_3)

                        df = pd.concat([df1, df2, df3], ignore_index=True)

                        # Transform the URL column
                        transformed_urls = df["url"].apply(transform_url)

                        url_file = f"url_output_{self.args.domain}.txt"
                        url_file_path = get_project_file_path("internal_results/url_results", f"{url_file}")

                        # Save the result to a new text file
                        with open(url_file_path, "w") as f:
                            for url in transformed_urls:
                                f.write(f"{url}\n")

                        self.existing_bots = sort_unique_values_in_file(url_file_path)

                        print(f"\nTransformed URLs saved to {url_file_path}")
                        print("\nChecking accessible CoPilot demo websites")

                        self.open_bots = run_pup_commands(self.existing_bots)

                        print("Done, results saved under final_results/chat_exists_output.txt")

                    else:
                        logging.error("Did not find a solution publisher prefix")

        elif self.args.tenant_id:

            self.default_env_found = True

            # Print the tenant's domain if available
            print_brand(self.args.tenant_id)

            ffuf_path_1 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{self.args.tenant_id}_one_word_names.csv")

            ffuf_path_2 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{self.args.tenant_id}_two_word_names.csv")

            ffuf_path_3 = get_project_file_path("internal_results/ffuf_results", f"ffuf_results_{self.args.tenant_id}.csv")

            ten_id = self.args.tenant_id.replace("-", "").replace("Default", "")
            env_bots_endpoint = f"https://default{ten_id[:-2]}.{ten_id[-2:]}.environment.api.powerplatform.com/powervirtualagents/botsbyschema/"
            logging.info(f"Endpoint for the environment ID bots schema: {env_bots_endpoint}")

            fuzz1_value = None
            fuzz_file_name = f"fuzz1_value_{self.args.tenant_id}.txt"
            fuzz_file_path = get_project_file_path("internal_results/prefix_fuzz_values", f"{fuzz_file_name}")

            print("Checking if an existing solution publisher prefix value exists for this domain.")

            # Check if the file exists
            if os.path.exists(fuzz_file_path):
                # Open the file and read the first line
                with open(fuzz_file_path, "r") as file:
                    first_line = file.readline().strip()  # .strip() removes any leading/trailing whitespace

                print("An existing publisher prefix value was found for this tenant, continuing to search for CoPilot demo websites.")

                if first_line:
                    self.default_solution_prefix_found = True
                    for line, popen in get_ffuf_results(
                        env_bots_endpoint,
                        f"{fuzz_file_path}",
                        "botname_1_no_capital.txt",
                        "botname_2_to_3_capital.txt",
                        "botname_2_to_3_capital.txt",
                        self.args.rate,
                        self.args.threads,
                        self.args.tenant_id,
                        ffuf_flag,
                        self.args.timeout_bots,
                    ):
                        print(line, end="")

                    logging.info(
                        f"FFUF executed successfully for the found solution publisher prefix, results saved to internal_results/ffuf_results/ffuf_results_{self.args.tenant_id}.txt"
                    )

                    df1 = pd.DataFrame()
                    df2 = pd.DataFrame()
                    df3 = pd.DataFrame()

                    # Read the CSV file
                    if os.path.exists(ffuf_path_1):
                        df1 = pd.read_csv(ffuf_path_1)

                    if os.path.exists(ffuf_path_2):
                        df2 = pd.read_csv(ffuf_path_2)

                    if os.path.exists(ffuf_path_3):
                        df3 = pd.read_csv(ffuf_path_3)

                    df = pd.concat([df1, df2, df3], ignore_index=True)

                    # Transform the URL column
                    transformed_urls = df["url"].apply(transform_url)

                    url_file = f"url_output_{self.args.tenant_id}.txt"
                    url_file_path = get_project_file_path("internal_results/url_results", f"{url_file}")

                    # Save the result to a new text file
                    with open(f"{url_file_path}", "w") as f:
                        for url in transformed_urls:
                            f.write(f"{url}\n")

                    self.existing_bots = sort_unique_values_in_file(f"{url_file_path}")

                    print(f"\nTransformed URLs saved to {url_file_path}")
                    print("\nChecking accessible CoPilot demo websites")

                    self.open_bots = run_pup_commands(self.existing_bots)

                    print("Done, results saved under final_results/chat_exists_output.txt")

                else:
                    logging.error("Did not find a default solution publisher prefix")

            else:
                print("No existing prefix value found for this tenant, starting solution publisher prefix scan.")
                logging.info("Running ffuf")

                for value, popen in get_ffuf_results_prefix(
                    env_bots_endpoint,
                    "prefix_wordlist_char_fix_basic.txt",
                    "suffix_wordlist_basic_1.txt",
                    self.args.rate,
                    self.args.threads,
                    self.args.timeout_prefix,
                ):
                    if value:
                        fuzz1_value = value
                        print("Found solution publisher prefix, proceeding to scan bot names")
                        break

                fuzz_file_name = f"fuzz1_value_{self.args.tenant_id}.txt"
                fuzz_file_path = get_project_file_path("internal_results/prefix_fuzz_values", f"{fuzz_file_name}")

                if fuzz1_value:
                    self.default_solution_prefix_found = True
                    with open(fuzz_file_path, "w") as file:
                        file.write(fuzz1_value + "\n")

                    # Continue with further logic using the new FUZZ1 wordlist
                    logging.info("Running ffuf with new FUZZ1 values")

                    for line, popen in get_ffuf_results(
                        env_bots_endpoint,
                        f"{fuzz_file_path}",
                        "botname_1_no_capital.txt",
                        "botname_2_to_3_capital.txt",
                        "botname_2_to_3_capital.txt",
                        self.args.rate,
                        self.args.threads,
                        self.args.tenant_id,
                        ffuf_flag,
                        self.args.timeout_bots,
                    ):
                        print(line, end="")

                    logging.info(
                        f"FFUF executed successfully for the found solution publisher prefix, results saved to internal_results/ffuf_results/ffuf_results_{self.args.tenant_id}.txt"
                    )

                    df1 = pd.DataFrame()
                    df2 = pd.DataFrame()
                    df3 = pd.DataFrame()

                    # Read the CSV file
                    if os.path.exists(ffuf_path_1):
                        df1 = pd.read_csv(ffuf_path_1)

                    if os.path.exists(ffuf_path_2):
                        df2 = pd.read_csv(ffuf_path_2)

                    if os.path.exists(ffuf_path_3):
                        df3 = pd.read_csv(ffuf_path_3)

                    df = pd.concat([df1, df2, df3], ignore_index=True)

                    # Transform the URL column
                    transformed_urls = df["url"].apply(transform_url)

                    url_file = f"url_output_{self.args.tenant_id}.txt"
                    url_file_path = get_project_file_path("internal_results/url_results", f"{url_file}")

                    # Save the result to a new text file
                    with open(url_file_path, "w") as f:
                        for url in transformed_urls:
                            f.write(f"{url}\n")

                    self.existing_bots = sort_unique_values_in_file(f"{url_file_path}")

                    print(f"\nTransformed URLs saved to {url_file_path}")
                    print("\nChecking accessible CoPilot demo websites")

                    self.open_bots = run_pup_commands(self.existing_bots)

                    print("Done, results saved under final_results/chat_exists_output.txt")

                else:
                    logging.error("Did not find a solution publisher prefix")

        self.dump_results()
