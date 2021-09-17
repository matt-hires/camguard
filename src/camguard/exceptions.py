
class CamGuardError(Exception):
    """
    exception base class for camguard module
    """

    def __init__(self, message: str):
        self._message = message

    @property
    def message(self) -> str:
        return self._message


class GDriveError(CamGuardError):
    """ indicates error with gdrive processing 
    """

    def __init__(self, message: str):
        super().__init__(message)

class ConfigurationError(CamGuardError):
    """ indicates wrong configuration
    """

    def __init__(self, message: str):
        super().__init__(message)
