from abc import ABC, abstractmethod
from typing import Callable, List


class MotionHandler(ABC):

    def __init__(self) -> None:
        self.__motion_finished = None

    @abstractmethod
    def on_motion(self) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

    @property
    def on_motion_finished(self) -> Callable[[List[str]], None]:
        return self.__motion_finished

    @on_motion_finished.setter
    def on_motion_finished(self, callback: Callable[[List[str]], None]) -> None:
        """set motion finished callback

        Args:
            callback (Callable[[List[str]], None]): callback function
        """
        self.__motion_finished = callback


class MotionDetector(ABC):
    @abstractmethod
    def detect_motion(self, handler: MotionHandler) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass
