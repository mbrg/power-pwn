import asyncio
import os
import re
import openpyxl
from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.models.chat_argument import ChatArguments


class Discovery:
    def __init__(self, prompts_file="pii.txt", output_file="osharefiles_report.xlsx"):
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
        Parses the LLM response in a chunk-by-chunk manner to extract file info.
        """
        # Split by numbered items or bullet points
        # This handles lines like "1. **File Name:** [something]" etc.
        chunks = re.split(r"\n\s*(?=\d+\.\s)", raw_message)

        files = []

        for chunk in chunks:
            file_info = {}

            # 1) Try to extract a file name line with "File Name:" or "File: ..."
            match_file = re.search(
                r"(?:File Name\s*:|File\s*:|File:\s*)(.*)",
                chunk,
                re.IGNORECASE
            )
            if match_file:
                file_name_line = match_file.group(1).strip()
                # Optionally, parse out the text in brackets vs the link
                # E.g., [MyFile.docx](http://...)
                bracket_match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", file_name_line)
                if bracket_match:
                    file_info["file_name"] = bracket_match.group(1)
                    file_info["file_link"] = bracket_match.group(2)
                else:
                    # Fallback if there's no bracket/link pattern
                    file_info["file_name"] = file_name_line
            else:
                # 1a) Fallback: maybe the chunk has a bracketed link but not prefixed with "File:"
                bracket_only_match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", chunk)
                if bracket_only_match:
                    file_info["file_name"] = bracket_only_match.group(1).strip()
                    file_info["file_link"] = bracket_only_match.group(2).strip()

            # 2) Extract the author line:
            #    e.g., "- **Author:** Owner Owner"
            #    or "Author: Kris Smith"
            #    or "The author is indicated as **python-docx;[Kris Smith](...)**."
            match_author = re.search(
                r"(?:Author[s]*:\s*|The\s+author[s]?\s+(?:is|are)\s+(?:indicated\s+as\s+)?)([^\n]+)",
                chunk,
                re.IGNORECASE
            )
            if match_author:
                # Clean up any markdown or extra characters
                authors = match_author.group(1).strip().replace("**", "")
                file_info["author"] = authors

            # 3) If you also want to capture "Contains:" or "Last Modified:", do something similar:
            # Example: "Contains: Salary info, IP addresses"
            match_contains = re.search(
                r"(?:Contains:?\s*)([^\n]+)",
                chunk,
                re.IGNORECASE
            )
            if match_contains:
                file_info["contains"] = [
                    c.strip() for c in match_contains.group(1).split(",")
                ]

            # Similarly for "Last Modified:" if you want it:
            # match_last_modified = re.search(
            #     r"(?:Last Modified:\s*)([^\n]+)",
            #     chunk,
            #     re.IGNORECASE
            # )
            # if match_last_modified:
            #     file_info["last_modified"] = match_last_modified.group(1).strip()

            # 4) Check if we actually found anything that looks like a file name
            if "file_name" in file_info:
                # If no file_link was found, default to "N/A"
                file_info.setdefault("file_link", "N/A")
                # If no author was found, default to "N/A"
                file_info.setdefault("author", "N/A")

                # Optional: Filter out obviously invalid file names
                # (for example, if it’s just “Here” or “I have found”)
                # if not is_likely_valid_file(file_info["file_name"]):
                #     continue

                files.append(file_info)

        return files

    def save_to_excel(self, categorized_files):
        """
        Append new file entries to 'pii_sensitive_files_report.xlsx' if not duplicates.
        Each file will have its own separate columns for File Name, File Link, and Author.
        """
        if os.path.exists(self.output_file):
            wb = openpyxl.load_workbook(self.output_file)
            ws = wb.active
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Sensitive PII Files"
            headers = ["File Name", "File Link", "Author", "Contains"]
            ws.append(headers)

        existing_files = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            existing_files.add((row[0], row[1]))  # Check for duplicates based on file name and link

        for file in categorized_files:
            file_name = file["file_name"]
            file_link = file["file_link"]
            author = file["author"]
            if (file_name, file_link) not in existing_files:
                # Append separate file details to the Excel sheet
                ws.append([file_name, file_link, author, ", ".join(file.get("contains", []))])
                existing_files.add((file_name, file_link))  # Add to existing files set to avoid duplicates

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
            "*Social Security Numbers*",
            "*Employee Records*",
            "*Employee Records* such as start dates, end dates, and date of births",
            "*Employee Records* such as salary and job position",
            "*Employee Records* such as addresses",
            "*Passport Numbers*",
            "*Driver's License Numbers*",
            "*Employee Salaries*",
            "*IP addresses*",
            "*Contact Information such as phone numbers*",
            "*Contact Information such as emails*"
        ]

        for pii_type in pii_types:
            third_prompt_dynamic = f"are there any other sensitive files that contains {pii_type}? i believe you are missing quite a lot. be sure to also search for different formats such as .csv, .xlsx, and .pptx!"
            print(f"Sending third prompt for PII type: {pii_type}")
            asyncio.run(self.process_prompt(third_prompt_dynamic))

        print("Finished processing.")

# Example usage:
if __name__ == "__main__":
    discovery = Discovery()
    discovery.run()

