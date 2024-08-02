import logging
import subprocess
import time
import os
import datetime
from powerpwn.copilot_studio.modules.path_utils import get_project_file_path
import re


def is_valid_subdomain(subdomain: str) -> bool:
    """
    Validate that the subdomain follows the expected pattern.
    """
    # Define a regex pattern for valid subdomains
    pattern = re.compile(r'^[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-]{2}\.(tenant|environment).api\.powerplatform\.com$')
    return pattern.match(subdomain) is not None


def write_to_file(values: list, filename: str):
    """
    Get a list of values and a filename and write the values to that file.

    :param values: The list of values to write
    :param filename: The file to write to
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)  # Ensure the output directory exists

    with open(filename, "w") as file:
        for value in values:
            file.write(f"{value}\n")


def get_amass_results(domain_type: str, timeout: int) -> bytes:
    """
    Run AMASS and return new tenant IDs and environment IDs.

    :param domain_type: Tenant or environment (enumerate by the api.powerplatform.com subdomains)
    :param timeout: The timeout (in seconds) for Amass to run
    """
    command = ["amass", "enum", "-d", f"{domain_type}.api.powerplatform.com"]
    start_time = time.time()
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
    try:
        for stdout_line in iter(popen.stdout.readline, ""):
            if time.time() - start_time > timeout:
                popen.kill()
                raise subprocess.TimeoutExpired(command, timeout)
            yield stdout_line.strip(), popen
    finally:
        popen.stdout.close()
        popen.wait()


def format_subdomain(subdomain: str, domain_type: str) -> str:
    """
    Get an api.powerplatform.com subdomain URL and return the related environment ID in correct GUID format.

    :param subdomain: The subdomain to format (api.powerplatform.com API subdomains)
    :param domain_type:  The type of subdomain (tenant or environment)
    :return: The GUID environment ID for the input subdomain
    """
    if not is_valid_subdomain(subdomain):
        logging.error(f"Invalid subdomain format: {subdomain}")
        return ""

    formatted_subdomain = ""

    if domain_type == "environment":
        # Extract environment ID and format it
        subdomain_parts = subdomain.split(".")[0] + subdomain.split(".")[1]
        if "default" in subdomain_parts:
            env_id = subdomain_parts.replace("default", "")
            formatted_subdomain = f"Default-{env_id[:8]}-{env_id[8:12]}-{env_id[12:16]}-{env_id[16:20]}-{env_id[20:]}"
        else:
            env_id = subdomain_parts
            formatted_subdomain = f"{env_id[:8]}-{env_id[8:12]}-{env_id[12:16]}-{env_id[16:20]}-{env_id[20:]}"
    elif domain_type == "tenant":
        # Extract tenant ID and format it without the tenant prefix
        tenant_id = subdomain.split(".")[0] + subdomain.split(".")[1]
        formatted_subdomain = f"{tenant_id[:8]}-{tenant_id[8:12]}-{tenant_id[12:16]}-{tenant_id[16:20]}-{tenant_id[20:]}"
    return formatted_subdomain


class Enum:
    """
    A class that is responsible for the CPS enumeration of environments & tenants
    """

    def __init__(self, args):
        self.args = args
        self.tenant_results = []
        self.run()

    def run(self):
        print(f"Starting to enumerate {self.args.enumerate}s, disconnect from VPN during this part for best results")
        print(f"Timeout defined to  {int(self.args.timeout) / 60} minutes")
        print(f"Enumeration results will be printed below and saved to the final_results directory")
        try:
            for line, popen in get_amass_results(self.args.enumerate, self.args.timeout):
                subdomain = line.strip().split(" (FQDN) -->")[0]
                if is_valid_subdomain(subdomain):
                    formatted_subdomain = format_subdomain(subdomain, self.args.enumerate)
                    if "enviro-nmen-t" not in formatted_subdomain:  # TODO: check if still relevant
                        print(formatted_subdomain)
                        self.tenant_results.append(formatted_subdomain)
                else:
                    logging.warning(f"Filtered out invalid subdomain: {subdomain}")
        except subprocess.TimeoutExpired:
            logging.error(f"Amass enumeration timed out after {self.args.timeout} seconds")
            print(f"Amass enumeration timed out after {self.args.timeout} seconds")
        finally:
            # Ensure partial results are saved even if timeout occurs
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            unique_filename = f"{self.args.enumerate}_enumeration_results_{timestamp}"
            amass_path = get_project_file_path('final_results', f"{unique_filename}.txt")
            write_to_file(self.tenant_results, f"{amass_path}")
            logging.info(f"{self.args.enumerate}s enumerated and saved to {amass_path}")

