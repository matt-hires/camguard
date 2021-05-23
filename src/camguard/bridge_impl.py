from abc import ABC, abstractmethod
from typing import Callable, List, Optional

""" Handler Bridge """


class MotionHandlerImpl(ABC):
    """abstract base class for motion handler implementations
    """

    @abstractmethod
    def handle_motion(self) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

    @property
    def after_handling(self) -> Optional[Callable[[List[str]], None]]:
        if not hasattr(self, "_after_handling"):
            return None
        return self._after_handling

    @after_handling.setter
    def after_handling(self, handler: Optional[Callable[[List[str]], None]]) -> None:
        """set after handling callback

        Args:
            handler (Callable[[List[str]], None]): callback function
        """
        self._after_handling = handler


""" Detector Bridge """


class MotionDetectorImpl(ABC):
    """abstract base class for motion detector implementations
    """
    @abstractmethod
    def on_motion(self, handler: Callable[[], None]) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass



""" FileStorage Bridge """


class FileStorageImpl(ABC):
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
