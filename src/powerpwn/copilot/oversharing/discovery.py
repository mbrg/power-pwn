import os
import asyncio
import json
import openpyxl
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector

# Function to read prompts from the prompts.txt file
def read_prompts_from_file(file_path="pii.txt"):
    prompts = {}
    with open(file_path, "r") as f:
        content = f.read().strip().split("\n\n")
        for section in content:
            lines = section.split("\n", 1)
            if len(lines) == 2:
                prompts[lines[0].strip(":")] = lines[1].strip()
    return prompts

# Categorize files based on PII content
def categorize_files(files):
    """Categorize files based on PII content."""
    pii_keywords = ['social security number', 'passport numbers', 'drivers license numbers', 'employee records', 'contact information']

    categorized_data = []

    for file in files:
        file_info = {
            'file_name': file.get('Title', 'Unknown'),
            'author': file.get('Author', 'Unknown'),
            'last_modified': file.get('LastModifiedTime', 'Unknown'),
            'contains': []  # New field to store what the file contains
        }

        file_name = file_info['file_name'].lower()

        # Check for PII-related keywords in the file name
        for keyword in pii_keywords:
            if keyword.lower() in file_name:
                file_info['contains'].append(keyword)

        if file_info['contains']:
            categorized_data.append(file_info)

    return categorized_data

def save_to_excel(categorized_files):
    """Save the categorized files data to an Excel spreadsheet."""
    output_file = "pii_sensitive_files_report.xlsx"
    if os.path.exists(output_file):
        wb = openpyxl.load_workbook(output_file)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sensitive PII Files"
        headers = ['File Name', 'Author', 'Last Modified', 'Contains']
        ws.append(headers)

    for file in categorized_files:
        row = [file['file_name'], file['author'], file['last_modified'], ", ".join(file['contains'])]
        ws.append(row)

    wb.save(output_file)
    print(f"Excel file updated: {output_file}")

# Function to save the response to a .txt file
def save_response_to_txt(response, file_name="response.txt"):
    """Save the raw response to a text file."""
    # Check if the response is a tuple (e.g., it could be something like (message, status))
    if isinstance(response, tuple):
        response = response[0]  # Extract the string from the tuple if it's a tuple

    # Now response should be a string
    with open(file_name, "a") as f:
        f.write(response + "\n")
    print(f"Response saved to {file_name}")


# Set environment variables for M365 user credentials
user = os.getenv('m365user')
user_password = os.getenv('m365pass')

if user is None or user_password is None:
    raise ValueError("Environment variables for email or password are not set.")

args = ChatArguments(
    user=user,
    password=user_password,
    verbose=VerboseEnum.full,
    scenario=CopilotScenarioEnum.officeweb,
    use_cached_access_token=False
)

copilot_connector = CopilotConnector(args)
copilot_connector.init_connection()

# Read prompts from the file
prompts = read_prompts_from_file("pii.txt")

# Send initial prompt to get started
print("Sending initial prompt to Copilot...")
result = asyncio.get_event_loop().run_until_complete(asyncio.gather(copilot_connector.connect(prompts['init_prompt'])))
if result[0]:
    print(result[0].parsed_message)
    save_response_to_txt(result[0].parsed_message)

# Send second prompt to list sensitive files
print("Sending second prompt to Copilot...")
result = asyncio.get_event_loop().run_until_complete(asyncio.gather(copilot_connector.connect(prompts['second_prompt'])))
if result[0]:
    raw_message = result[0].parsed_message
    print("Raw Response (Second Prompt):", raw_message)
    save_response_to_txt(raw_message)

    try:
        raw_message_str = raw_message.copilot_message
        json_str = raw_message_str.split('```json\n')[1].split('\n```')[0]
        files_with_pii = json.loads(json_str)

        categorized_files = categorize_files(files_with_pii)
        print("Categorized Files (Second Prompt):", categorized_files)

        save_to_excel(categorized_files)

    except (IndexError, json.JSONDecodeError) as e:
        print("Error parsing the JSON response:", e)

# Loop to continuously ask for more PII-related files
while True:
    print("Sending third prompt to get more PII-related files...")
    result = asyncio.get_event_loop().run_until_complete(asyncio.gather(copilot_connector.connect(prompts['third_prompt'])))

    if result[0]:
        raw_message = result[0].parsed_message
        print("Raw Response (Third Prompt):", raw_message)
        save_response_to_txt(raw_message)

        try:
            raw_message_str = raw_message.copilot_message

            if 'None' in raw_message_str:
                print("No more PII files found. Exiting...")
                break

            json_str = raw_message_str.split('```json\n')[1].split('\n```')[0]
            more_files = json.loads(json_str)

            if more_files:
                categorized_files = categorize_files(more_files)
                print("Categorized Files (Third Prompt):", categorized_files)

                save_to_excel(categorized_files)
            else:
                print("No additional files found in response.")

        except (IndexError, json.JSONDecodeError) as e:
            print("Error parsing the JSON response:", e)









