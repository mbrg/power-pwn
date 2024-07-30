class CopilotConnectionFailedException(Exception):
    """
    Exception raised when failing to get access token to connect to copilot.

    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)
