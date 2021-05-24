import logging
from typing import Callable

from gpiozero import MotionSensor as GPIOMotionSensor # type: ignore

from .bridge_impl import MotionDetectorImpl

LOGGER = logging.getLogger(__name__)


class RaspiGpioSensor(MotionDetectorImpl):
    """ Class for wrapping python motion sensor
    """

    def __init__(self, gpio_pin: int) -> None:
        """ default ctor

        Args:
            gpio_pin (int): gpio pin where the motion sensor is connected
        """
        super().__init__()
        LOGGER.debug(f"Configuring motion sensor on pin {gpio_pin}")
        self._motion_sensor = GPIOMotionSensor(gpio_pin)

    def register_handler(self, handler: Callable[..., None]) -> None:
        """abstract base method for calling on motion callback

        Args:
            handler (MotionHandler): motion handler callback 
        """
        LOGGER.debug(f"Registering motion_sensor callback")
        self._motion_sensor.when_activated = handler

    def shutdown(self) -> None:
        LOGGER.debug(f"Shutting down")
        # shutdown motion sensor thread and join
        self._motion_sensor.close()
