import logging
from typing import Callable, Optional

from gpiozero import LED, MotionSensor as GPIOMotionSensor # type: ignore

from camguard.motion_detector_settings import RaspiGpioSensorSettings

from .bridge_impl import MotionDetectorImpl

LOGGER = logging.getLogger(__name__)


class RaspiGpioSensor(MotionDetectorImpl):
    """ Class for wrapping python motion sensor
    """

    def __init__(self, settings: RaspiGpioSensorSettings) -> None:
        super().__init__()

        LOGGER.info(f"Using motion sensor on pin {settings.gpio_pin_number}")
        self.__motion_sensor = GPIOMotionSensor(pin=settings.gpio_pin_number,
                                               queue_len=settings.queue_length,
                                               sample_rate=settings.sample_rate,
                                               threshold=settings.threshold)

        self.__settings = settings
        self.__motion_sensor.when_activated = self.__when_activated
        self.__motion_sensor.when_deactivated = self.__when_deactivated
        self.__handler: Optional[Callable[..., None]] = None

        self.__led: Optional[LED] = None
        if settings.led_gpio_pin_number > 0:
            self.__led = LED(settings.led_gpio_pin_number)

        # store activation status
        self._activated = False 

    def register_handler(self, handler: Callable[..., None]) -> None:
        LOGGER.debug("Registering motion_sensor callback")
        self.__handler = handler

    def shutdown(self) -> None:
        LOGGER.info("Shutting down")
        # shutdown motion sensor thread and join
        self.__motion_sensor.close()

    @property
    def id(self) -> int:
        return self.__settings.gpio_pin_number

    def __when_activated(self) -> None:
        if self.disabled:
            LOGGER.debug("Sensor disabled, activation signal ignored")
            return

        self._activated = True
        LOGGER.debug("Sensor activated")

        if self.__led: 
            self.__led.on()

        if self.__handler:
            self.__handler()

    def __when_deactivated(self) -> None:
        # when disabled, still check activation flag - in case of disable between activation cycle
        if self.disabled and not self._activated:
            LOGGER.debug("Sensor disabled, deactivation signal ignored")
            return

        self._activated = False
        LOGGER.debug("Sensor deactivated")

        if self.__led:
            self.__led.off()
