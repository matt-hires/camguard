from abc import ABC, abstractmethod

class MotionHandler(ABC):
    @abstractmethod
    def on_motion(self) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

class MotionDetector(ABC):
    @abstractmethod
    def detect_motion(self, handler: MotionHandler) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass
