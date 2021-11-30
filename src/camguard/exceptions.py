
class CamguardError(Exception):
    """
    exception base class for camguard module
    """

    def __init__(self, message: str):
        super().__init__()
        self._message = message

    @property
    def message(self) -> str:
        return self._message


class GDriveError(CamguardError):
    """ indicates error with gdrive processing 
    """

class ConfigurationError(CamguardError):
    """ indicates wrong configuration
    """
