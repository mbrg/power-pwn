from typing_extensions import override

from powerpwn.copilot.loggers.ilogger import ILogger


class ConsoleLogger(ILogger):
    @override
    def log(self, message: str) -> None:
        print(message)
