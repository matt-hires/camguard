from abc import ABC, abstractmethod
from typing import Any, Callable, List

# Handler Bridge


class MotionHandlerImpl(ABC):
    """abstract base class for motion handler implementations
    """

    @abstractmethod
    def handle_motion(self) -> Any:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

    @property
    @abstractmethod
    def id(self) -> int:
        pass


# Detector Bridge

class MotionDetectorImpl(ABC):
    """abstract base class for motion detector implementations
    """

    def __init__(self) -> None:
        self._disabled = False

    @abstractmethod
    def register_handler(self, handler: Callable[..., None]) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

    @property
    @abstractmethod
    def id(self) -> int:
        pass

    @property
    def disabled(self) -> bool:
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._disabled = value


# FileStorage Bridge


class FileStorageImpl(ABC):
    """abstract base class for file storage implementations
    """
    @abstractmethod
    def authenticate(self) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def enqueue_files(self, files: List[str]) -> None:
        pass

    @property
    @abstractmethod
    def id(self) -> int:
        pass


# MailClient Bridge


class MailClientImpl(ABC):
    """abstract base class for mail notification implementations
    """

    @abstractmethod
    def send_mail(self, files: List[str]) -> None:
        pass


# NetworkDeviceDetector Bridge


class NetworkDeviceDetectorImpl(ABC):
    """abstract base class for network detector implementations
    """

    @abstractmethod
    def init(self) -> None:
        pass

    @abstractmethod
    def register_handler(self, handler: Callable[..., None]) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
