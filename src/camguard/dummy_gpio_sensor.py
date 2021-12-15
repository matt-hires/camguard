
import logging
from random import uniform
from threading import Event, Lock, Thread
from typing import Callable, ClassVar, Optional

from camguard.motion_detector_settings import DummyGpioSensorSettings

from .exceptions import CamguardError

from .bridge_impl import MotionDetectorImpl

LOGGER = logging.getLogger(__name__)


class DummySensorThread(Thread):
    """simulate motion sensor by triggering handler in a random interval between two boundaries
    """
    _lock: Lock = Lock()

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.__stop_event = Event()
        self.__max_trigger_seconds: float = 10.0
        self.__min_trigger_seconds: float = 5.0
        self.__handler: Optional[Callable[..., None]] = None

    @property
    def handler(self) -> Optional[Callable[..., None]]:
        with DummySensorThread._lock:
            return self.__handler

    @handler.setter
    def handler(self, value: Callable[..., None]) -> None:
        with DummySensorThread._lock:
            self.__handler = value

    def run(self) -> None:
        self.__stop_event.clear()
        try:
            while not self.__stop_event.wait(round(uniform(self.__min_trigger_seconds,
                                                          self.__max_trigger_seconds), 1)):
                LOGGER.debug("Simulating motion detection")
                if self.handler: 
                    self.handler() # skipcq: PYL-E1102
        # skipcq: PYL-W0703
        except Exception as e:
            LOGGER.exception("Unrecoverable error in dummy gpio sensor thread", exc_info=e)

        LOGGER.info("Finished")

    def stop(self, timeout_sec: float = 4.0) -> None:
        if not self.is_alive():
            LOGGER.debug("Thread has already been stopped")
            return
        LOGGER.info("Shutting down gracefully")
        self.__stop_event.set()
        self.join(timeout_sec)
        if self.is_alive():
            msg = f"Failed to stop within {timeout_sec}"
            LOGGER.error(msg)
            raise CamguardError(msg)


class DummyGpioSensor(MotionDetectorImpl):
    """dummy gpio sensor implementation
    this can be used for running camguard in a dummy mode
    """
    __id: ClassVar[int] = 0

    # skipcq: PYL-W0613
    def __init__(self, settings: DummyGpioSensorSettings) -> None:
        super().__init__()

        self.__sensor_thread = DummySensorThread()
        self.__sensor_thread.start()
        self.__sensor_thread.handler = self.__when_activated
        self.__handler: Optional[Callable[..., None]] = None
        DummyGpioSensor.__id += 1

    def register_handler(self, handler: Callable[..., None]) -> None:
        self.__handler = handler

    def shutdown(self) -> None:
        self.__sensor_thread.stop()

    def __when_activated(self) -> None:
        if self.disabled:
            LOGGER.debug("Sensor disabled, activation ignored")
            return
        if self.__handler:
            self.__handler()

    @property
    def id(self) -> int:
        return DummyGpioSensor.__id
