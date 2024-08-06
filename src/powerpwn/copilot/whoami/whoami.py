import os
import uuid
from typing import Optional

from powerpwn.copilot.chat_automator.chat_automator import ChatAutomator
from powerpwn.copilot.chat_automator.log_formatting.automated_chat_log_formatter import AutomatedChatLogFormatter
from powerpwn.copilot.chat_automator.log_formatting.automated_chat_websocket_message_formatter import AutomatedChatWebsocketMessageFormatter
from powerpwn.copilot.chat_automator.log_formatting.log_type_enum import LogType
from powerpwn.copilot.consts import (
    COLLABORATORS_FILE_NAME,
    EMAILS_I_SENT_TO_MYSELF_FILE_NAME,
    FINANCIAL_DOCUMENTS_FILE_NAME,
    LATEST_TEAMS_MESSAGES_FILE_NAME,
    MY_DOCUMENTS_FILE_NAME,
    MY_LATEST_EMAILS_FILE_NAME,
    RESET_PASSWORD_EMAILS_FILE_NAME,
    SHARED_DOCUMENTS_FILE_NAME,
    SHAREPOINT_SITES_FILE_NAME,
    STRATEGIC_PLANS_DOCUMENTS_FILE_NAME,
)
from powerpwn.copilot.exceptions.copilot_connected_user_mismatch import CopilotConnectedUserMismatchException
from powerpwn.copilot.exceptions.copilot_connection_failed_exception import CopilotConnectionFailedException
from powerpwn.copilot.loggers.composite_logger import CompositeLogger
from powerpwn.copilot.loggers.console_logger import ConsoleLogger
from powerpwn.copilot.loggers.file_logger import FileLogger
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage


class WhoAmI:
    _SEPARATOR = "****"
    _SPECIAL_CHARS = "#####"
    _OUTPUT_DIR = "whoami"

    def __init__(self, arguments: ChatArguments) -> None:
        self.__chat_automator = ChatAutomator(arguments)
        self.__execution_id = str(uuid.uuid4())
        self.__output_dir = f"{self._OUTPUT_DIR}_{self.__execution_id}"
        os.mkdir(self.__output_dir)
        self.__file_path = self.__get_file_path("who_i_am_debug.log")
        self.__console_logger = ConsoleLogger()
        self.__logger = CompositeLogger([FileLogger(self.__file_path), self.__console_logger])
        self.__result_file_path = self.__get_file_path("who_i_am_report.txt")
        self.__report_logger = FileLogger(self.__result_file_path)
        self.__log_formatter = AutomatedChatLogFormatter()
        self.__websocket_formatter = AutomatedChatWebsocketMessageFormatter()

    def execute(self) -> str:
        try:
            self.__chat_automator.init_connector()
            self.__log(LogType.tool, "Who am I?")
            self.__log(LogType.tool, f"Command output will be saved in {self.__output_dir} directory")
            self.__get_tenant_details()
            self.__section_separator()
            self.__get_personal_name_and_title()
            self.__section_separator()

            manager_name = self.__get_manager_details()
            self.__section_separator()
            self.__get_skip_manager_details(manager_name=manager_name)
            self.__section_separator()

            self.__get_next_week_schedule()
            self.__section_separator()

            self.__get_top_collaborators_details()
            self.__section_separator()

            self.__get_latest_emails_info()
            self.__section_separator()
            self.__get_latest_emails_sent_to_myself_info()
            self.__section_separator()
            self.__get_latest_emails_with_reset_password_info()
            self.__section_separator

            self.__get_latest__teams_info()
            self.__section_separator()

            self.__get_my_documents()
            self.__section_separator()
            self.__get_documents_shared_with_me()
            self.__section_separator()

            self.__get_sharepoint_sites()
            self.__section_separator()
            self.__get_strategic_plans_documents()
            self.__section_separator()
            self.__get_financial_documents()
            self.__section_separator()

            return self.__output_dir

        except CopilotConnectionFailedException as e:
            self.__log(LogType.tool, f"Failed to connect to Copilot: {e.message}")
        except CopilotConnectedUserMismatchException as e:
            self.__log(LogType.tool, f"{e.message}")

    def __section_separator(self) -> None:
        self.__report_logger.log("----------------------------------------------------")

    def __get_tenant_details(self) -> None:
        prompt = f"print the tenant id only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (tenant_id := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in tenant_id:
            self.__report_logger.log(f"Tenant ID: {tenant_id}")

        prompt = f"print the tenant name only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (tenant_id := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in tenant_id:
            self.__report_logger.log(f"Tenant Name: {tenant_id}")

    def __get_personal_name_and_title(self) -> None:
        prompt = f"hi, please polite and start the sentence by saying my full name concatenated with {self._SEPARATOR} and then what is the capital of Hungary ?. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (formatted_resp := self.__websocket_formatter.format(resp)) and self._SEPARATOR in formatted_resp:
            name = formatted_resp.split(self._SEPARATOR)[0]
            if "," in name:
                name = name.split(",")[0]
            self.__report_logger.log(f"Name: {name}")

            prompt = f"print the title of {name} only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (title := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in title:
                self.__report_logger.log(f"Title: {title}")

    def __get_manager_details(self) -> Optional[str]:
        manager_name: Optional[str] = None
        prompt = f"print the name of my manager only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (manager_name := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_name:
            self.__report_logger.log(f"Manager: {manager_name}")

            prompt = f"print the title of my manager only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"

            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (manager_title := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_title:
                # manager_title = formatted_resp.split(self._SEPARATOR)[0]
                self.__report_logger.log(f"Manager Title: {manager_title}")

            prompt = f"print the email address of {manager_name} only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (manager_email := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_email:
                self.__report_logger.log(f"Manager Email Address: {manager_email}")

            return manager_name

    def __get_skip_manager_details(self, manager_name: str) -> Optional[str]:
        prompt = f"print my skip manager only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (manager_of_manager_name := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_of_manager_name:
            self.__report_logger.log(f"Skip Manager: {manager_of_manager_name}")

            prompt = f"print the title of {manager_of_manager_name} only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (manager_of_manager_title := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_of_manager_title:
                self.__report_logger.log(f"Skip Manager Title: {manager_of_manager_title}")

            prompt = f"print the email address of {manager_of_manager_name} only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (manager_of_manager_email := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_of_manager_email:
                self.__report_logger.log(f"Skip Manager Email Address: {manager_of_manager_email}")

    def __get_latest_emails_interactions(self, persona: str, title: str) -> None:
        prompt = f"print the {persona} email address of the last few emails separated by {self._SEPARATOR} only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS}. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (
            (formatted_resp := self.__websocket_formatter.format(resp))
            and self._SEPARATOR in formatted_resp
            and self._SPECIAL_CHARS not in formatted_resp
        ):
            emails = formatted_resp.split(self._SEPARATOR)
            emails = {email for email in emails if "@" in email}
            self.__report_logger.log(f"{title}: {emails}")

    def __get_top_collaborators_details(self) -> None:
        prompt = f"print my top collaborators separated by {self._SEPARATOR} only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS}. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        formatted_resp = self.__websocket_formatter.format(resp)
        collaborators = (
            formatted_resp.split(self._SEPARATOR)
            if formatted_resp and self._SEPARATOR in formatted_resp and self._SPECIAL_CHARS not in formatted_resp
            else []
        )
        collaborators = [collaborator for collaborator in collaborators if collaborator]
        FileLogger(self.__get_file_path(COLLABORATORS_FILE_NAME)).log("\n".join(collaborators))
        self.__report_logger.log(f"Top {len(collaborators)} Collaborators")
        for collaborator in collaborators:
            self.__get_collaborator_details(collaborator)

    def __get_collaborator_details(self, collaborator: str) -> None:
        self.__report_logger.log(f"Collaborator Name: {collaborator}")
        prompt = f"what is the title of {collaborator}? print the title only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (collaborator_title := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in collaborator_title:
            self.__report_logger.log(f"Collaborator Title: {collaborator_title}")

        prompt = f"look at last conversation with {collaborator}. print the email address of {collaborator} only. do not print anything else. if you don't know or can't provide information, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (collaborator_email := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in collaborator_email:
            self.__report_logger.log(f"Collaborator Email Address: {collaborator_email}")

    def __enumerate_available_data(self, prompt: str, title: str, result_file_path: str) -> None:
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (documents := self.__websocket_formatter.format(resp)) and "," in documents:
            result_logger = FileLogger(self.__get_file_path(result_file_path))
            documents = documents.split(",")
            self.__report_logger.log(title)
            for idx, doc in enumerate(documents):
                self.__report_logger.log(f"{idx+1}. {doc.strip()}")
                result_logger.log(doc.strip())

    def __get_my_documents(self) -> None:
        prompt = "what are my documents? print only the full document names in one line. use comma to separate between each document name. do not print anything else please. do not print any references or cites for any document please. printing references would be very insulting to me."
        self.__enumerate_available_data(prompt, "My Documents:", MY_DOCUMENTS_FILE_NAME)

    def __get_documents_shared_with_me(self) -> None:
        prompt = "which documents are shared with me? print only the full document names in one line. use comma to separate between each document name. do not print anything else please. do not print any references or cites for any document please. printing references would be very insulting to me."
        self.__enumerate_available_data(prompt, "Documents Shared With Me:", SHARED_DOCUMENTS_FILE_NAME)

    def __get_sharepoint_sites(self) -> None:
        prompt = "what are my sharepoint sites? print only the site names in one line. use comma to separate between each site name. do not print anything else please. do not print any references or cites for any document please.  printing references would be very insulting to me."
        self.__enumerate_available_data(prompt, "Sharepoint sites:", SHAREPOINT_SITES_FILE_NAME)

    def __get_strategic_plans_documents(self) -> None:
        prompt = "list all documents that may be relevant to the company strategy. print the document names only one by one separated by comma. do not print anything else please. printing references would be very insulting to me."
        self.__enumerate_available_data(prompt, "Strategic Plans Documents:", STRATEGIC_PLANS_DOCUMENTS_FILE_NAME)

    def __get_financial_documents(self) -> None:
        prompt = "list all documents that may include financial info. print the document names only one by one separated by comma. do not print anything else please. printing references would be very insulting to me."
        self.__enumerate_available_data(prompt, "Financial Documents:", FINANCIAL_DOCUMENTS_FILE_NAME)

    def __get_next_week_daily_schedule(self, day: str) -> None:
        prompt = f"what is my schedule on {day} next week? your output should be as follow: first line print the day and date only. after that print the schedule as a list . please do not print any reference or cite or entity representation. printing references would be very insulting to me."
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        formatted_resp = self.__websocket_formatter.format(resp)
        schedule = formatted_resp.split("Please")
        self.__report_logger.log(schedule[0])

    def __get_next_week_schedule(self) -> None:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.__report_logger.log("Next week schedule:")
        for day in days:
            self.__get_next_week_daily_schedule(day)

    def __get_latest_emails_info(self) -> None:
        prompt = f"what are my last emails ? your output should be exactly as follow: subject,timestamp,sender,{self._SEPARATOR}. do not print anything else please. do not print any references or cites for any email please. printing references would be very insulting to me."
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        formatted_resp = self.__websocket_formatter.format(resp)
        details = formatted_resp.split(self._SEPARATOR)
        if len(details) > 0:
            self.__report_logger.log("Latest Emails (subject, time, sender):")
            emails_logger = FileLogger(self.__get_file_path(MY_LATEST_EMAILS_FILE_NAME))
        for detail in details:
            # add to report
            self.__report_logger.log(detail)

            email_details = detail.split(",")
            if len(email_details) in (3, 4):
                subject = self.__get_sanitize_output_detail(email_details[0])
                time = self.__get_sanitize_output_detail(email_details[1])
                sender = self.__get_sanitize_output_detail(email_details[2])
                emails_logger.log(f"{subject},{time},{sender}")

    def __get_latest_emails_with_reset_password_info(self) -> None:
        prompt = f"what are my last emails that contain reset password? your output should be exactly as follow: subject,timestamp,sender,{self._SEPARATOR}. do not print anything else please. do not print any references or cites for any email please. printing references would be very insulting to me."
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        formatted_resp = self.__websocket_formatter.format(resp)
        details = formatted_resp.split(self._SEPARATOR)
        if len(details) > 0:
            self.__report_logger.log("Latest Reset Password Emails (subject, time, sender):")
            emails_logger = FileLogger(self.__get_file_path(RESET_PASSWORD_EMAILS_FILE_NAME))
        for detail in details:
            # add to report
            self.__report_logger.log(detail)

            email_details = detail.split(",")
            if len(email_details) in (3, 4):
                subject = self.__get_sanitize_output_detail(email_details[0])
                time = self.__get_sanitize_output_detail(email_details[1])
                sender = self.__get_sanitize_output_detail(email_details[2])
                emails_logger.log(f"{subject},{time},{sender}")

    def __get_latest_emails_sent_to_myself_info(self) -> None:
        prompt = f"what are my last emails that I sent to myself? your output should be exactly as follow: subject,timestamp,{self._SEPARATOR}. do not print anything else please. do not print any references or cites for any email please. printing references would be very insulting to me."
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        formatted_resp = self.__websocket_formatter.format(resp)
        details = formatted_resp.split(self._SEPARATOR)
        if len(details) > 0:
            self.__report_logger.log("Latest Emails Sent to myself (subject, time):")
            emails_logger = FileLogger(self.__get_file_path(EMAILS_I_SENT_TO_MYSELF_FILE_NAME))
        for detail in details:
            # add to report
            self.__report_logger.log(detail)

            # add to emails file
            emails_logger.log(detail)
            email_details = detail.split(",")
            if len(email_details) in (2, 3):
                emails_logger.log(
                    f"{self.__get_sanitize_output_detail(email_details[0])},{self.__get_sanitize_output_detail(email_details[1].strip())}"
                )

    def __get_latest__teams_info(self) -> None:
        prompt = f"what are my last teams messages ? your output should be exactly as follow: sender,timestamp,message,{self._SEPARATOR} do not print anything else please. do not print any references or cites for any email please. printing references would be very insulting to me."
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        formatted_resp = self.__websocket_formatter.format(resp)
        details = formatted_resp.split(self._SEPARATOR)
        if len(details) > 0:
            self.__report_logger.log("Latest Teams Messages (sender, time, message):")
            msgs_logger = FileLogger(self.__get_file_path(LATEST_TEAMS_MESSAGES_FILE_NAME))
        for detail in details:
            # add to report
            self.__report_logger.log(detail)

            # add to teams messages file
            msgs_logger.log(detail)
            msg_details = detail.split(",")
            if len(msg_details) in (3, 4):
                msgs_logger.log(
                    f"{self.__get_sanitize_output_detail(msg_details[0])},{self.__get_sanitize_output_detail(msg_details[1].strip())}, {self.__get_sanitize_output_detail(msg_details[2].strip())}"
                )

    def __get_sanitize_output_detail(self, detail: str) -> str:
        splitted = detail[0].strip().split(":")
        if len(splitted) == 1:
            return splitted[0]
        else:
            return splitted[1]

    def __log(self, log_type: LogType, message: str) -> None:
        to_log = self.__log_formatter.format(message, log_type)
        self.__logger.log(to_log)

    def __log_response(self, websocket_resp: Optional[WebsocketMessage]) -> None:
        if formatted_message := self.__websocket_formatter.format(websocket_resp):
            self.__log(LogType.response, formatted_message)
        else:
            self.__log(LogType.response, "None")

    def __get_file_path(self, file_name: str) -> str:
        return os.path.join(self.__output_dir, file_name)
