from camguard.exceptions.camguard_error import CamGuardError


class GDriveError(CamGuardError):
    """ indicates error with gdrive processing 
    """

    def __init__(self, message: str):
        self._message = message

    @property
    def message(self) -> str:
        return self._message
