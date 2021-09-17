
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

class ConfigurationError(CamGuardError):
    """ indicates wrong configuration
    """
