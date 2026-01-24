class ApiError(Exception):
    def __init__(self, title: str, message: str, status_code: int):
        self.title = title
        self.message = message
        self.status_code = status_code
