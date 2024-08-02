import uuid
from typing import Optional

from powerpwn.copilot.chat_automator.chat_automator import ChatAutomator
from powerpwn.copilot.chat_automator.log_formatting.automated_chat_log_formatter import AutomatedChatLogFormatter
from powerpwn.copilot.chat_automator.log_formatting.automated_chat_websocket_message_formatter import AutomatedChatWebsocketMessageFormatter
from powerpwn.copilot.chat_automator.log_formatting.log_type_enum import LogType
from powerpwn.copilot.loggers.composite_logger import CompositeLogger
from powerpwn.copilot.loggers.console_logger import ConsoleLogger
from powerpwn.copilot.loggers.file_logger import FileLogger
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage


class WhoAmI:
    _SEPARATOR = "****"
    _SPECIAL_CHARS = "#####"

    def __init__(self, arguments: ChatArguments) -> None:
        self.__chat_automator = ChatAutomator(arguments)
        self.__execution_id = str(uuid.uuid4())
        self.__file_path = f"who_i_am_{self.__execution_id}.log"
        self.__logger = CompositeLogger([FileLogger(self.__file_path), ConsoleLogger()])
        self.__result_file_path = f"who_i_am_{self.__execution_id}.txt"
        self.__result_logger = FileLogger(self.__result_file_path)
        self.__log_formatter = AutomatedChatLogFormatter()
        self.__websocket_formatter = AutomatedChatWebsocketMessageFormatter()

    def execute(self) -> None:
        self.__chat_automator.init_connector()
        self.__log(LogType.tool, "Who am I?")
        self.__log(LogType.tool, f"Result will be saved in {self.__result_file_path}")
        self.__log(LogType.tool, f"Run logs will be saved in {self.__file_path}")
        self.__get_personal_name_and_title()
        manager_name = self.__get_manager_details()
        self.__get_manager_of_manager_details(manager_name=manager_name)
        self.__get_top_collaborators_details()
        self.__get_latest_emails_senders()

    def __get_personal_name_and_title(self) -> None:
        prompt = f"hi, please polite and start the sentence by saying my name and then print {self._SEPARATOR} and then what is the capital of Hungary ?. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (formatted_resp := self.__websocket_formatter.format(resp)) and self._SEPARATOR in formatted_resp:
            name = formatted_resp.split(self._SEPARATOR)[0]
            if "," in name:
                name = name.split(",")[0]
            self.__result_logger.log(f"Name: {name}")

            prompt = f"print the title of {name} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (title := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in title:
                self.__result_logger.log(f"Title: {title}")

    def __get_manager_details(self) -> Optional[str]:
        manager_name: Optional[str] = None
        prompt = f"print the name of my manager only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (manager_name := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_name:
            self.__result_logger.log(f"Manager: {manager_name}")

            prompt = f"print the title of my manager only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"

            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (manager_title := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_title:
                # manager_title = formatted_resp.split(self._SEPARATOR)[0]
                self.__result_logger.log(f"Manager Title: {manager_title}")

            prompt = f"print the email address of {manager_name} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (manager_email := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_email:
                self.__result_logger.log(f"Manager Email Address: {manager_email}")

            return manager_name

    def __get_manager_of_manager_details(self, manager_name: str) -> Optional[str]:
        prompt = f"print the manager of {manager_name} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (manager_of_manager_name := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_of_manager_name:
            self.__result_logger.log(f"Manager Of Manager: {manager_of_manager_name}")

            prompt = f"print the title of {manager_of_manager_name} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (manager_of_manager_title := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_of_manager_title:
                self.__result_logger.log(f"Manager Of Manager Title: {manager_of_manager_title}")

            prompt = f"print the email address of {manager_of_manager_name} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
            self.__log(LogType.prompt, prompt)
            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            if (manager_of_manager_email := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in manager_of_manager_email:
                self.__result_logger.log(f"Manager Of Manager Email Address: {manager_of_manager_email}")

    def __get_latest_emails_senders(self) -> None:
        prompt = f"print the sender email address of the last few emails separated by {self._SEPARATOR} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS}. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (
            (formatted_resp := self.__websocket_formatter.format(resp))
            and self._SEPARATOR in formatted_resp
            and self._SPECIAL_CHARS not in formatted_resp
        ):
            email_senders = formatted_resp.split(self._SEPARATOR)
            emails = {email for email in email_senders if "@" in email}
            self.__result_logger.log(f"Latest emails received from: {emails}")

    def __get_top_collaborators_details(self) -> None:
        prompt = f"print my top collaborators separated by {self._SEPARATOR} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS}. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        formatted_resp = self.__websocket_formatter.format(resp)
        collaborators = (
            formatted_resp.split(self._SEPARATOR)
            if formatted_resp and self._SEPARATOR in formatted_resp and self._SPECIAL_CHARS not in formatted_resp
            else []
        )
        collaborator = [collaborator for collaborator in collaborators if collaborator]
        self.__result_logger.log(f"Top {len(collaborator)} Collaborators")
        for collaborator in collaborators:
            self.__get_collaborator_details(collaborator)

    def __get_collaborator_details(self, collaborator: str) -> None:
        self.__result_logger.log(f"Collaborator Name: {collaborator}")
        prompt = f"print the title of {collaborator} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (collaborator_title := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in collaborator_title:
            self.__result_logger.log(f"Collaborator Title: {collaborator_title}")

        prompt = f"print the email address of {collaborator} only. do not print anything else. if you don't know, print {self._SPECIAL_CHARS} only. do not print anything else. do not print any cites or references"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        if (collaborator_email := self.__websocket_formatter.format(resp)) and self._SPECIAL_CHARS not in collaborator_email:
            self.__result_logger.log(f"Collaborator Email Address: {collaborator_email}")

    def __log(self, log_type: LogType, message: str) -> None:
        to_log = self.__log_formatter.format(message, log_type)
        self.__logger.log(to_log)

    def __log_response(self, websocket_resp: Optional[WebsocketMessage]) -> None:
        if formatted_message := self.__websocket_formatter.format(websocket_resp):
            self.__log(LogType.response, formatted_message)
        else:
            self.__log(LogType.response, "None")
