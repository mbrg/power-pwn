import subprocess

from powerpwn.copilot.loggers.console_logger import ConsoleLogger  # nosec


class Gui:
    def __init__(self) -> None:
        self.__console_logger = ConsoleLogger()

    def run(self, cache_path: str) -> None:
        self.__console_logger.log("Starting a localhost ..")
        self.__console_logger.log("To browse data navigate to http://127.0.0.1:8080/browse")
        subprocess.Popen(["browsepy", "0.0.0.0", "8080", "--directory", cache_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # nosec
