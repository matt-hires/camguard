
import logging
from random import uniform
from threading import Event, Lock, Thread
from typing import Callable, Optional

from camguard.settings import DummyGpioSensorSettings

from .exceptions import CamGuardError

from .bridge_impl import MotionDetectorImpl

LOGGER = logging.getLogger(__name__)


class DummySensorThread(Thread):
    """simulate motion sensor by triggering handler in a random interval
    """
    _lock: Lock = Lock()

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self._stop_event = Event()

    @property
    def handler(self) -> Optional[Callable[..., None]]:
        with DummySensorThread._lock:
            if not hasattr(self, "_handler"):
                return None
            return self._handler

    @handler.setter
    def handler(self, value: Callable[..., None]) -> None:
        with DummySensorThread._lock:
            self._handler = value

    def run(self) -> None:
        self._stop_event.clear()
        try:
            while not self._stop_event.wait(round(uniform(1, 3), 1)):
                LOGGER.debug(f"Simulating motion detection")
                if hasattr(self, "_handler"):
                    if self.handler:
                        self.handler()
        except Exception as e:
            LOGGER.error("Unrecoverable error in dummy gpio sensor thread", exc_info=e)

        LOGGER.info("Finished")

    def stop(self, timeout_sec: float = 4.0) -> None:
        if not self.is_alive():
            LOGGER.debug("Thread has already been stopped")
            return
        LOGGER.info("Shutting down gracefully")
        self._stop_event.set()
        self.join(timeout_sec)
        if self.is_alive():
            msg = f"Failed to stop within {timeout_sec}"
            LOGGER.error(msg)
            raise CamGuardError(msg)


class DummyGpioSensor(MotionDetectorImpl):
    def __init__(self, settings: DummyGpioSensorSettings) -> None:
        self._sensor_thread = DummySensorThread()
        self._sensor_thread.start()
        self._settings = settings

    def register_handler(self, handler: Callable[..., None]) -> None:
        self._sensor_thread.handler = handler

    def shutdown(self) -> None:
        self._sensor_thread.stop()

    @property
    def id(self) -> int:
        return self._settings.gpio_pin_number
