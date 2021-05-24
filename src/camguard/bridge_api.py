from functools import wraps
from typing import Any, Callable, Generator, List

from .bridge_impl import FileStorageImpl, MotionDetectorImpl, MotionHandlerImpl
from .dummy_gpio_sensor import LOGGER
from .settings import (FileStorageSettings, ImplementationType,
                       MotionDetectorSettings, MotionHandlerSettings)


def pipelinestep(func: Callable[..., Any]):
    """interceptor function for priming coroutines 
    before first usage. In this context it is used to declare a motion handler
    pipeline step. Simply put @motionhandler above function 
    to use it
    """
    @wraps(func)  # make it look like the wrapped 'func'
    def _wrapper(*args: Any, **kwargs: Any) -> Generator[Any, Any, Any]:
        gen = func(*args, **kwargs)
        next(gen)
        return gen
    return _wrapper


""" Handler Bridge """


class MotionHandler:
    """ motion handler api which supports handler pipeline 
    """

    def __init__(self, record_root_path: str) -> None:
        self._record_root_path: str = record_root_path

    def init(self) -> None:
        self._settings = MotionHandlerSettings.load_settings()
        self._get_impl()

    @pipelinestep
    def on_motion(self, pipeline: List[Generator[None, Any, None]]
                  ) -> Generator[None, "MotionDetector", None]:
        """ motion handler pipeline step: on_motion
        handle current motion event in handler and sends return value to sink pipeline

        Yields:
            Generator[None, object, None]: motiondetector object which detected motion
        """
        while True:
            detector: MotionDetector = (yield)
            LOGGER.info(f"Detected motion on gpio pin: {detector.gpio_pin}")
            ret_val = self._get_impl().handle_motion()
            for step in pipeline:
                step.send(ret_val)

    def stop(self) -> None:
        self._get_impl().shutdown()

    def _get_impl(self) -> MotionHandlerImpl:
        if not hasattr(self, "_impl"):
            if self._settings.impl_type == ImplementationType.DUMMY:
                from .dummy_cam import DummyCam
                self._impl = DummyCam(self._record_root_path)
            else:
                # defaults to raspi cam implementation
                from .raspi_cam import RaspiCam
                self._impl = RaspiCam(self._record_root_path)

        return self._impl


""" Detector Bridge """


class MotionDetector:
    """ motion detector api, which supports handler pipeline 
    """

    def __init__(self, gpio_pin: int) -> None:
        self._gpio_pin: int = gpio_pin
        self._pipeline: List[Generator[None, "MotionDetector", None]] = []

    def init(self) -> None:
        """initialize motion detector and construct implementation depending on settings
        """
        self._settings: MotionDetectorSettings = MotionDetectorSettings.load_settings()
        self._get_impl()

    def register_handlers(self, pipeline: List[Generator[None, "MotionDetector", None]]
                          ) -> None:
        """register handler pipe

        Args:
            pipeline (List[Generator[None, object, None]]): array of gen based 
            coroutines to build a handler pipe which will be called when motion occurs 
        """
        self._pipeline = pipeline
        self._get_impl().register_handler(self._on_motion)

    def stop(self) -> None:
        """shutdown sensor, stops motion detection 
        """
        self._get_impl().shutdown()

    @property
    def gpio_pin(self) -> int:
        return self._gpio_pin

    def _on_motion(self) -> None:
        for step in self._pipeline:
            step.send(self)

    def _get_impl(self) -> MotionDetectorImpl:
        if not hasattr(self, "_impl"):
            if self._settings.impl_type == ImplementationType.DUMMY:
                from .dummy_gpio_sensor import DummyGpioSensor
                self._impl = DummyGpioSensor(self._gpio_pin)
            else:
                # defaults to raspi cam implementation
                from .raspi_gpio_sensor import RaspiGpioSensor
                self._impl = RaspiGpioSensor(self._gpio_pin)

        return self._impl


""" FileStorage Bridge """


class FileStorage:
    """ file storage api, which supports handler pipeline 
    """

    def __init__(self) -> None:
        self._settings: FileStorageSettings = FileStorageSettings.load_settings()

    def authenticate(self) -> None:
        """authenticate to storage
        """
        self._get_impl().authenticate()

    def start(self) -> None:
        """start storage worker
        """
        self._get_impl().start()

    def stop(self) -> None:
        """stop storage worker
        """
        self._get_impl().stop()

    @pipelinestep
    def enqueue_files(self) -> Generator[None, List[str], None]:
        """motion handler pipeline step: enqueue files 

        Yields:
            Generator[None, List[str], None]: file path array which will be enqueued
        """
        while True:
            files: List[str] = (yield)
            self._get_impl().enqueue_files(files)

    def _get_impl(self) -> FileStorageImpl:
        if not hasattr(self, "_impl"):
            if self._settings.impl_type == ImplementationType.DUMMY:
                from .gdrive_dummy_storage import GDriveDummyStorage
                self._impl = GDriveDummyStorage()
            else:
                # defaults to gdrive implementation
                from .gdrive_storage import GDriveStorage
                self._impl = GDriveStorage()

        return self._impl
