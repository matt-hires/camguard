from abc import ABC, abstractmethod
from typing import Callable, List

from camguard.settings import ImplementationType, MotionDetectorSettings, MotionHandlerSettings


""" Handler Bridge """


class MotionHandlerImpl(ABC):
    def __init__(self) -> None:
        self._after_handling = None

    @abstractmethod
    def handle_motion(self) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass

    @property
    def after_handling(self) -> Callable[[List[str]], None]:
        return self._after_handling

    @after_handling.setter
    def after_handling(self, handler: Callable[[List[str]], None]) -> None:
        """set after handling callback

        Args:
            handler (Callable[[List[str]], None]): callback function
        """
        self._after_handling = handler


class MotionHandler:
    def __init__(self, record_root_path: str) -> None:
        self._record_root_path = record_root_path
        self._settings: MotionHandlerSettings = None
        self._impl: MotionHandlerImpl = None

    def handle_motion(self)-> None:
        self._get_impl().handle_motion()

    def init(self) -> None:
        self._settings: MotionHandlerSettings = MotionHandlerSettings.load_settings()
        self._get_impl()

    def stop(self) -> None:
        self._get_impl().shutdown()

    def after_handling(self, handler: Callable[[List[str]], None]) -> None:
        self._get_impl().after_handling = handler

    def _get_impl(self) -> MotionHandlerImpl:
        if not self._impl:
            if self._settings.impl_type == ImplementationType.DUMMY:
                # TODO implement dummy
                pass
            else:
                # defaults to raspi cam implementation
                from camguard.raspi_cam import RaspiCam
                self._impl = RaspiCam(self._record_root_path)

        return self._impl


""" Detector Bridge """


class MotionDetectorImpl(ABC):
    @abstractmethod
    def on_motion(self, handler: Callable) -> None:
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass


class MotionDetector:
    def __init__(self, gpio_pin: int) -> None:
        self._gpio_pin: int = gpio_pin
        self._settings: MotionDetectorSettings = None
        self._impl: MotionDetectorImpl = None

    def init(self) -> None:
        self._settings: MotionDetectorSettings = MotionDetectorSettings.load_settings()
        self._get_impl()

    def on_motion(self, handler: Callable) -> None:
        self._get_impl().on_motion(handler)

    def stop(self) -> None:
        self._get_impl().shutdown()

    def _get_impl(self) -> MotionDetectorImpl:
        if not self._impl:
            if self._settings.impl_type == ImplementationType.DUMMY:
                # TODO implement dummy
                pass
            else:
                # defaults to raspi cam implementation
                from camguard.raspi_gpio_sensor import RaspiGpioSensor
                self._impl = RaspiGpioSensor(self._gpio_pin)

        return self._impl


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


class FileStorage:
    def __init__(self) -> None:
        self._impl: FileStorageImpl = None

    def authenticate(self) -> None:
        self._get_impl().authenticate()

    def start(self) -> None:
        self._get_impl().start()

    def stop(self) -> None:
        self._get_impl().stop()

    def enqueue_files(self, files: List[str]) -> None:
        self._get_impl().enqueue_files(files)

    def _get_impl(self) -> FileStorageImpl:
        if self._impl:
            return self._impl

        from camguard.gdrive_storage import GDriveStorage
        self._impl = GDriveStorage()
        return self._impl
