import logging

from gpiozero import MotionSensor as GPIOMotionSensor
from camguard.motion import MotionDetector, MotionHandler

LOGGER = logging.getLogger(__name__)


class MotionSensor(MotionDetector):
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

    def detect_motion(self, handler: MotionHandler) -> None:
        """abstract base method for calling on motion callback

        Args:
            handler (MotionHandler): motion handler for handling detection events 
        """
        LOGGER.debug(f"Registering motion_sensor callback")
        self._motion_sensor.when_activated = handler.on_motion

    def shutdown(self) -> None:
        LOGGER.debug(f"Shutting down motion sensor")
        self._motion_sensor.close()
