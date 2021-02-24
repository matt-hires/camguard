from camguard.exceptions.error import Error


class ConfigurationError(Error):
    """ indicates wrong configuration
    """

    def __init__(self, message: str):
        self._message = message

    @property
    def message(self) -> str:
        return self._message
