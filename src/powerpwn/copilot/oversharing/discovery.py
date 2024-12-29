import os
import asyncio
import json
import re
import openpyxl
from datetime import datetime

# -- powerpwn/copilot imports --
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector

def read_prompts_from_file(file_path="pii.txt"):
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


def enhanced_parser(raw_message):
    """
    Extracts file_name, link, and author from free-text, Markdown, or structured formats.
    """
    extracted_files = []

    # Use regex to find file details in free-text or Markdown-like formats
    file_pattern = re.compile(
        r"\*\*File Name:\*\*\s*(?P<file_name>.*?)\n.*?"
        r"\*\*Author:\*\*\s*(?P<author>.*?)\n.*?"
        r"\*\*Link:\*\*\s*\[.*?\]\((?P<link>.*?)\)",
        re.DOTALL
    )

    # Match all occurrences of the pattern
    matches = file_pattern.finditer(raw_message)
    for match in matches:
        extracted_files.append({
            'file_name': match.group('file_name').strip(),
            'link': match.group('link').strip(),
            'author': match.group('author').strip(),
        })

    # Fallback: Find lines that match individual fields if no comprehensive match found
    if not extracted_files:
        print("DEBUG: No structured matches found. Attempting fallback extraction.")
        file_lines = raw_message.splitlines()
        current_file = {}

        for line in file_lines:
            if "File Name:" in line:
                current_file['file_name'] = line.split("File Name:")[1].strip()
            elif "Author:" in line:
                current_file['author'] = line.split("Author:")[1].strip()
            elif "Link:" in line and '(' in line:
                link_match = re.search(r'\((.*?)\)', line)
                if link_match:
                    current_file['link'] = link_match.group(1).strip()

            # If all fields are populated, add to extracted_files and reset
            if all(k in current_file for k in ['file_name', 'link', 'author']):
                extracted_files.append(current_file)
                current_file = {}

    return extracted_files


def save_to_excel(categorized_files):
    """
    Append new file entries to 'pii_sensitive_files_report.xlsx' if not duplicates.
    """
    output_file = "new_pii_sensitive_files_report.xlsx"
    if os.path.exists(output_file):
        wb = openpyxl.load_workbook(output_file)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sensitive PII Files"
        headers = ['File Name - Link', 'Author', 'Contains']
        ws.append(headers)

    existing_files = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        existing_files.add((row[0], row[1]))

    for file in categorized_files:
        file_name_link = file['file_name'] + " - " + file['link']
        if (file_name_link, file['author']) not in existing_files:
            ws.append([
                file_name_link,
                file['author'],
                ", ".join(file.get('contains', []))
            ])
    wb.save(output_file)
    print(f"Excel file updated: {output_file}")


def handle_response(raw_message):
    """
    Processes the raw response using the enhanced parser.
    """
    # Check if raw_message is a WebsocketParsedMessage object
    if hasattr(raw_message, 'copilot_message'):
        raw_message = raw_message.copilot_message  # Extract the actual message

    if not isinstance(raw_message, str):
        raise TypeError("raw_message must be a string or an object containing a message string.")

    extracted_files = enhanced_parser(raw_message)
    print("DEBUG: Extracted files:", extracted_files)
    return extracted_files



# ---------------- MAIN SCRIPT ----------------

if __name__ == "__main__":
    user = os.getenv('m365user')
    user_password = os.getenv('m365pass')
    if user is None or user_password is None:
        raise ValueError("Environment variables 'm365user' or 'm365pass' are not set.")

    args = ChatArguments(
        user=user,
        password=user_password,
        verbose=VerboseEnum.full,
        scenario=CopilotScenarioEnum.officeweb,
        use_cached_access_token=False
    )

    copilot_connector = CopilotConnector(args)
    copilot_connector.init_connection()

    # Read prompts
    prompts = read_prompts_from_file("pii.txt")
    print("DEBUG: prompts ->", prompts)

    # Initial Prompt
    print("Sending initial prompt to Copilot...")
    result = asyncio.get_event_loop().run_until_complete(
        asyncio.gather(copilot_connector.connect(prompts['init_prompt']))
    )
    if result and result[0]:
        print(result)
        print(result[0].parsed_message)
        raw_message = result[0].parsed_message
        print("Raw Response (Second Prompt):", raw_message)
        files_list = handle_response(raw_message)
        if files_list:
            save_to_excel(files_list)

    # Second Prompt
    print("Sending second prompt to Copilot...")
    result = asyncio.get_event_loop().run_until_complete(
        asyncio.gather(copilot_connector.connect(prompts['second_prompt']))
    )
    if result and result[0]:
        raw_message = result[0].parsed_message
        print("Raw Response (Second Prompt):", raw_message)
        files_list = handle_response(raw_message)
        if files_list:
            save_to_excel(files_list)

    # Dynamic Third Prompts
    pii_types = [
        'Social Security Numbers',
        'Employee Records such as start date, end date, salary, position',
        'Passport Numbers',
        'Driver\'s License Numbers',
        '*Employee Salaries*',
        '*IP addresses*',
        'Contact Information such as phone numbers, emails, addresses'
    ]

    try:
        for pii_type in pii_types:
            print(f"Sending third prompt for PII type: {pii_type}")
            third_prompt_dynamic = f"Great job! are there any other files of filetype (docx, csv, xlsx, or pptx) that you have didn't mention that contains *{pii_type}* or *emails*? If yes, please list them as well. Make sure to NOT MISS ANY FILE"
            result = asyncio.get_event_loop().run_until_complete(
                asyncio.gather(copilot_connector.connect(third_prompt_dynamic))
            )

            if result and result[0]:
                raw_message = result[0].parsed_message
                print(f"Raw Response for {pii_type}:", raw_message)
                files_list = handle_response(raw_message)
                if files_list:
                    save_to_excel(files_list)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting gracefully.")

    print("Finished processing.")














