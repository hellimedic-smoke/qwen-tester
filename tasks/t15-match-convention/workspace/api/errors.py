class ApiError(Exception):
    """An error returned to API clients, carrying a stable machine-readable code."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
