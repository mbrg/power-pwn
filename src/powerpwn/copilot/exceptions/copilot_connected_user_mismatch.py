class CopilotConnectedUserMismatchException(Exception):
    """
    Exception raised when used cached token user does not match the requested user.
    """

    def __init__(self, message):
        self.message = message
        super().__init__(message)
