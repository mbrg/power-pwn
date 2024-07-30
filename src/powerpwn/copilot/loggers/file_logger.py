from typing_extensions import override

from powerpwn.copilot.enums.message_type_enum import MessageTypeEnum
from powerpwn.copilot.enums.verbose_enum import VerboseEnum
from powerpwn.copilot.loggers.ilogger import ILogger
from powerpwn.copilot.websocket_message.websocket_message import WebsocketMessage


class FileLogger(ILogger):
    def __init__(self, file_path: str, verbose: VerboseEnum):
        self.__file_path = file_path
        self.__verbose = verbose

    @override
    def log(self, message: WebsocketMessage) -> None:
        if self.__verbose == VerboseEnum.off:
            return None

        elif (self.__verbose == VerboseEnum.mid and message.type() != MessageTypeEnum.copilot) or self.__verbose == VerboseEnum.full:
            with open(self.__file_path, "a") as file:
                file.write(message.message + "\n")
