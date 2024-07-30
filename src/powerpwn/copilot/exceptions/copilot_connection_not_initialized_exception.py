class CopilotConnectionNotInitializedException(Exception):
    """
    Exception raised when starting a chat with the copilot without initializing the connection.

    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)
