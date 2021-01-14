import logging
from typing import Callable

from gpiozero import MotionSensor

LOGGER = logging.getLogger(__name__)


class MotionSensorAdapter:
    """
    Adapter for wrapping python motion sensor
    """

    def __init__(self, gpio_pin: int):
        """
        default ctor
        :param gpio_pin: gpio pin where the motion sensor is connected
        """
        LOGGER.debug(f"Configuring motion sensor on pin {gpio_pin}")
        self.motion_sensor = MotionSensor(gpio_pin)

    def detect_motion(self, callback: Callable) -> None:
        """
        detect motion by using sensor on given pin and call function on movement
        :param callback: function to call on motion
        """
        self.motion_sensor.when_activated = callback
