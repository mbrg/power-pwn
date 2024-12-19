import os
import openpyxl
import re
import asyncio
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.enums.copilot_scenario_enum import CopilotScenarioEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.chat_automator.chat_automator import ChatAutomator
from powerpwn.copilot.copilot_connector.copilot_connector import CopilotConnector

# Set environment variables (if not already set)
user = os.getenv('m365user')
user_password = os.getenv('m365pass')
third_prompt = os.getenv('thirdprompt')

if user is None or user_password is None:
    raise ValueError("Environment variables for email or password are not set.")

print("User being looked at is:", user)

args = ChatArguments(
    user=user,
    password=user_password,
    verbose=VerboseEnum.full,
    scenario=CopilotScenarioEnum.officeweb,
    use_cached_access_token=False
)

copilot_connector = CopilotConnector(args)
copilot_connector.init_connection()

# Load the Excel file and extract file names
def extract_file_names_from_excel(file_path):
    """
    Extracts file names from the 'File Name' column in the Excel sheet.
    It uses regex to capture the portion inside the square brackets.
    """
    file_names = []
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    # Assuming the first row contains headers, and file names are in the first column (index 0)
    for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):  # Skip header row
        file_name = row[0].value
        if file_name:
            match = re.search(r'\[(.*?)\]', file_name)  # Extract text inside []
            if match:
                file_names.append(match.group(1))  # Append the extracted file name
    return file_names


async def get_file_content_and_save(file_name):
    """
    Request Copilot to print out the content of the file and save it to a .txt file.
    """
    prompt = f"I want to make an internal email regarding '{file_name}' to discuss any numbers or figures listed and insights gained and would love it if you drafted the email for me. Would be good to answer any possible FAQs with specific figures etc."

    # Send the request to Copilot
    result = await copilot_connector.connect(prompt)

    # Check if the result contains a valid message
    if hasattr(result, 'parsed_message') and result.parsed_message:
        raw_message = result.parsed_message
        print(f"Content retrieved for {file_name}:")
        print(raw_message.copilot_message)  # Display the content

        # Save the content to a text file
        with open(f"{file_name}.txt", "w") as txt_file:
            txt_file.write(raw_message.copilot_message)  # Write the actual message content to the file
        print(f"Content of {file_name} saved as {file_name}.txt")
    else:
        print(f"Failed to retrieve content for {file_name}.")


# Main script to extract file names and retrieve content for each file
async def main():
    # Load the Excel file and extract file names
    file_names = extract_file_names_from_excel("sensitive_files_report.xlsx")
    print("Extracted file names:", file_names)

    # For each file name, request content from Copilot and save it to a text file
    for file_name in file_names:
        await get_file_content_and_save(file_name)

# Run the async script
if __name__ == "__main__":
    asyncio.run(main())
