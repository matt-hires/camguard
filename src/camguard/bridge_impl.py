from abc import ABC, abstractmethod
from typing import Any, Callable, List, Tuple

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

    def on_disable(self, ips: List[Tuple[str, bool]]) -> None:
        disabled = False
        if ips: 
            # disable if any of the configured devices could be found on network
            disabled = bool([ip for ip in ips if ip[1]])

        self._disabled = disabled 


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
    def register_handler(self, handler: Callable[[List[Tuple[str, bool]]], None]) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass
