from camguard.exceptions.error import Error


class InputError(Error):
    """
    cam guard input exception
    """

    def __init__(self, message: str):
        """
        default ctor with message
        :param message: message string
        """
        self._message = message

    @property
    def message(self) -> str:
        """
        get error message
        """
        return self._message
