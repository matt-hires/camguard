import logging
from typing import Callable

from gpiozero import MotionSensor as GPIOMotionSensor
from camguard.bridge import MotionDetector

LOGGER = logging.getLogger(__name__)


class RaspiGpioSensor(MotionDetector):
    """ Class for wrapping python motion sensor
    """

    def __init__(self, gpio_pin: int) -> None:
        """ default ctor

        Args:
            gpio_pin (int): gpio pin where the motion sensor is connected
        """
        super().__init__(gpio_pin)
        LOGGER.debug(f"Configuring motion sensor on pin {gpio_pin}")
        self._motion_sensor = GPIOMotionSensor(gpio_pin)

    def on_motion(self, handler: Callable) -> None:
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
