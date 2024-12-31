import asyncio
import os
import re
import openpyxl
from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.models.chat_argument import ChatArguments


class Discovery:
    def __init__(self, prompts_file="pii.txt", output_file="new_pii_sensitive_files_report.xlsx"):
        self.prompts_file = prompts_file
        self.output_file = output_file
        self.user = os.getenv("m365user")
        self.user_password = os.getenv("m365pass")

        if not self.user or not self.user_password:
            raise ValueError("Environment variables 'm365user' or 'm365pass' are not set.")

        self.args = ChatArguments(
            user=self.user, password=self.user_password, verbose=VerboseEnum.full, scenario=CopilotScenarioEnum.officeweb, use_cached_access_token=False
        )
        self.copilot_connector = CopilotConnector(self.args)
        self.prompts = self.read_prompts_from_file(self.prompts_file)

    def read_prompts_from_file(self, file_path):
        """
        Reads prompts from the file. Expects sections separated by two newlines.
        """
        prompts = {}
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

            # Split on double newlines
            sections = content.split("\n\n")
            for section in sections:
                lines = section.split("\n", 1)
                if len(lines) == 2:
                    key = lines[0].strip(":").strip()
                    value = lines[1].strip()
                    prompts[key] = value
                else:
                    print(f"Warning: Skipping invalid section: {section}")
        return prompts

    def enhanced_parser(self, raw_message):
        """
        Extracts file_name, link, and author from free-text, Markdown, or structured formats.
        """
        extracted_files = []

        # Use regex to find file details in free-text or Markdown-like formats
        file_pattern = re.compile(
            r"\*\*File Name:\*\*\s*(?P<file_name>.*?)\n.*?" r"\*\*Author:\*\*\s*(?P<author>.*?)\n.*?" r"\*\*Link:\*\*\s*\[.*?\]\((?P<link>.*?)\)",
            re.DOTALL,
        )

        # Match all occurrences of the pattern
        matches = file_pattern.finditer(raw_message)
        for match in matches:
            extracted_files.append(
                {"file_name": match.group("file_name").strip(), "link": match.group("link").strip(), "author": match.group("author").strip()}
            )

        # Fallback: Find lines that match individual fields if no comprehensive match found
        if not extracted_files:
            print("DEBUG: No structured matches found. Attempting fallback extraction.")
            file_lines = raw_message.splitlines()
            current_file = {}

            for line in file_lines:
                if "File Name:" in line:
                    current_file["file_name"] = line.split("File Name:")[1].strip()
                elif "Author:" in line:
                    current_file["author"] = line.split("Author:")[1].strip()
                elif "Link:" in line and "(" in line:
                    link_match = re.search(r"\((.*?)\)", line)
                    if link_match:
                        current_file["link"] = link_match.group(1).strip()

                # If all fields are populated, add to extracted_files and reset
                if all(k in current_file for k in ["file_name", "link", "author"]):
                    extracted_files.append(current_file)
                    current_file = {}

        return extracted_files

    def save_to_excel(self, categorized_files):
        """
        Append new file entries to 'pii_sensitive_files_report.xlsx' if not duplicates.
        """
        if os.path.exists(self.output_file):
            wb = openpyxl.load_workbook(self.output_file)
            ws = wb.active
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Sensitive PII Files"
            headers = ["File Name - Link", "Author", "Contains"]
            ws.append(headers)

        existing_files = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            existing_files.add((row[0], row[1]))

        for file in categorized_files:
            file_name_link = file["file_name"] + " - " + file["link"]
            if (file_name_link, file["author"]) not in existing_files:
                ws.append([file_name_link, file["author"], ", ".join(file.get("contains", []))])
        wb.save(self.output_file)
        print(f"Excel file updated: {self.output_file}")

    def handle_response(self, raw_message):
        """
        Processes the raw response using the enhanced parser.
        """
        # Check if raw_message is a WebsocketParsedMessage object
        if hasattr(raw_message, "copilot_message"):
            raw_message = raw_message.copilot_message  # Extract the actual message

        if not isinstance(raw_message, str):
            raise TypeError("raw_message must be a string or an object containing a message string.")

        extracted_files = self.enhanced_parser(raw_message)
        print("DEBUG: Extracted files:", extracted_files)
        return extracted_files

    async def process_prompt(self, prompt):
        """
        Sends a prompt to Copilot and handles the response.
        """
        print(f"Sending prompt: {prompt}")
        result = await asyncio.gather(self.copilot_connector.connect(prompt))

        if result and result[0]:
            raw_message = result[0].parsed_message
            print(f"Raw Response: {raw_message}")
            files_list = self.handle_response(raw_message)
            if files_list:
                self.save_to_excel(files_list)

    def run(self):
        """
        The main method to run the entire discovery process.
        """
        # Initialize connection to Copilot
        self.copilot_connector.init_connection()

        # Process initial and second prompts
        asyncio.run(self.process_prompt(self.prompts["init_prompt"]))
        asyncio.run(self.process_prompt(self.prompts["second_prompt"]))

        # Dynamic third prompts
        pii_types = [
            "Social Security Numbers",
            "Employee Records such as start date, end date, salary, position",
            "Passport Numbers",
            "Driver's License Numbers",
            "*Employee Salaries*",
            "*IP addresses*",
            "Contact Information such as phone numbers, emails, addresses",
        ]

        for pii_type in pii_types:
            third_prompt_dynamic = f"Great job! are there any other files of filetype (docx, csv, xlsx, or pptx) that you have didn't mention that contains *{pii_type}* or *emails*? If yes, please list them as well. Make sure to NOT MISS ANY FILE"
            print(f"Sending third prompt for PII type: {pii_type}")
            asyncio.run(self.process_prompt(third_prompt_dynamic))

        print("Finished processing.")

# Example usage:
if __name__ == "__main__":
    discovery = Discovery()
    discovery.run()

