import logging
from typing import Callable

from gpiozero import MotionSensor as GPIOMotionSensor  # type: ignore

from .bridge_impl import MotionDetectorImpl
from .settings import RaspiGpioSensorSettings

LOGGER = logging.getLogger(__name__)


class RaspiGpioSensor(MotionDetectorImpl):
    """ Class for wrapping python motion sensor
    """

    def __init__(self, settings: RaspiGpioSensorSettings) -> None:
        LOGGER.info(f"Using motion sensor on pin {settings.gpio_pin_number}")
        self._motion_sensor = GPIOMotionSensor(settings.gpio_pin_number)
        self._settings = settings

    def register_handler(self, handler: Callable[..., None]) -> None:
        LOGGER.debug(f"Registering motion_sensor callback")
        self._motion_sensor.when_activated = handler

    def shutdown(self) -> None:
        LOGGER.info(f"Shutting down")
        # shutdown motion sensor thread and join
        self._motion_sensor.close()

    @property
    def id(self) -> int:
        return self._settings.gpio_pin_number
