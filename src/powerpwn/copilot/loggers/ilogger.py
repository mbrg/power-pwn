from abc import ABC, abstractmethod


class ILogger(ABC):
    @abstractmethod
    def log(self, message: str) -> None:
        """
        logs a message

        :param message: message to log
        """
