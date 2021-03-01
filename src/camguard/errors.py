
class CamGuardError(Exception):
    """
    exception base class for camguard module
    """
    pass

class GDriveError(CamGuardError):
    """ indicates error with gdrive processing 
    """

    def __init__(self, message: str):
        self._message = message

class ConfigurationError(CamGuardError):
    """ indicates wrong configuration
    """

    def __init__(self, message: str):
        self._message = message