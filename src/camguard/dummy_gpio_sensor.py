
import logging
from random import uniform
from threading import Event, Lock, Thread
from typing import Callable

from camguard.exceptions import CamGuardError

from .bridge import MotionDetectorImpl

LOGGER = logging.getLogger(__name__)


class DummySensorThread(Thread):
    """simulate motion sensor by triggering handler in a random interval
    """
    _lock: Lock = Lock()

    def __init__(self, handler: Callable = None) -> None:
        super().__init__(daemon=True)
        self._stop_event = Event()
        self._handler = handler

    @property
    def handler(self) -> Callable:
        with DummySensorThread._lock:
            return self._handler

    @handler.setter
    def handler(self, value: Callable) -> None:
        with DummySensorThread._lock:
            self._handler = value

    def run(self) -> None:
        self._stop_event.clear()
        try:
            while not self._stop_event.wait(round(uniform(1, 3), 1)):
                LOGGER.debug(f"Simulating motion detection")
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
    def __init__(self, gpio_pin: int) -> None:
        super().__init__()
        LOGGER.debug(f"Configuring dummy motion sensor on pin {gpio_pin}")
        self._sensor_thread = DummySensorThread()
        self._sensor_thread.start()

    def on_motion(self, handler: Callable) -> None:
        self._sensor_thread.handler = handler

    def shutdown(self) -> None:
        self._sensor_thread.stop()
