import datetime
import logging
import os
import re
import subprocess  # nosec
import time

from powerpwn.copilot_studio.modules.path_utils import get_project_file_path


def is_valid_subdomain(subdomain: str) -> bool:
    """
    Validate that the subdomain follows the expected pattern.
    """
    # Define a regex pattern for valid subdomains
    pattern = re.compile(r"^[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-]{2}\.(tenant|environment)\.api\.powerplatform\.com$")
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


def get_subfinder_results(domain_type: str, timeout: int) -> bytes:
    """
    Run subfinder and return new tenant IDs and environment IDs.

    :param domain_type: Tenant or environment (enumerate by the api.powerplatform.com subdomains)
    :param timeout: The timeout (in seconds) for subfinder to run
    """
    command = ["subfinder", "-d", f"{domain_type}.api.powerplatform.com", "-all", "-silent", "-timeout", str(timeout)]
    popen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)  # nosec
    try:
        for stdout_line in iter(popen.stdout.readline, ""):
            line = stdout_line.strip()
            # Skip empty lines
            if line:
                yield line, popen
    finally:
        popen.stdout.close()
        if popen.stderr:
            popen.stderr.close()
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

    def _check_subfinder_installed(self) -> bool:
        """Check if subfinder is installed."""
        from shutil import which

        if which("subfinder") is None:
            logging.error("❌ subfinder is not installed!")
            logging.error("")
            logging.error("Please install subfinder:")
            logging.error("  macOS: brew install subfinder")
            logging.error("  Linux: go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
            logging.error("  Or run: python init_repo.py --install-external-tools")
            return False
        return True

    def run(self):
        # Check if subfinder is installed
        if not self._check_subfinder_installed():
            return

        print(f"Starting to enumerate {self.args.enumerate}s")
        print(f"Timeout defined to  {int(self.args.timeout) / 60} minutes")
        print("Enumeration results will be printed below and saved to the final_results directory")
        print("=" * 80)
        print("")

        start_time = time.time()
        results_count = 0

        for line, popen in get_subfinder_results(self.args.enumerate, self.args.timeout):
            subdomain = line.strip()
            if is_valid_subdomain(subdomain):
                formatted_subdomain = format_subdomain(subdomain, self.args.enumerate)
                if "enviro-nmen-t" not in formatted_subdomain:  # TODO: check if still relevant
                    results_count += 1
                    elapsed_time = int(time.time() - start_time)
                    # Print in green for successful finds
                    print(f"\033[92m✓ [{results_count}] Found ({elapsed_time}s elapsed): {formatted_subdomain}\033[0m")
                    self.tenant_results.append(formatted_subdomain)
            else:
                logging.warning(f"Filtered out invalid subdomain: {subdomain}")

        # Ensure results are saved
        print("")
        print("=" * 80)
        total_time = int(time.time() - start_time)
        print(f"Enumeration completed in {total_time}s - Total results found: {results_count}")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unique_filename = f"{self.args.enumerate}_enumeration_results_{timestamp}"
        results_path = get_project_file_path("final_results", f"{unique_filename}.txt")
        write_to_file(self.tenant_results, f"{results_path}")
        logging.info(f"{self.args.enumerate}s enumerated and saved to {results_path}")
        print(f"Results saved to: {results_path}")
