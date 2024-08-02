from typing_extensions import override

from powerpwn.copilot.loggers.ilogger import ILogger


class FileLogger(ILogger):
    def __init__(self, file_path: str):
        self.__file_path = file_path

    @override
    def log(self, message: str) -> None:
        with open(self.__file_path, "a") as file:
            file.write(message + "\n\n")
