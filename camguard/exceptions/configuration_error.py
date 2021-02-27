from camguard.exceptions.camguard_error import CamGuardError


class ConfigurationError(CamGuardError):
    """ indicates wrong configuration
    """

    def __init__(self, message: str):
        self._message = message

    @property
    def message(self) -> str:
        return self._message
