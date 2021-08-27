import logging
from typing import Callable

from gpiozero import LED, MotionSensor as GPIOMotionSensor  # type: ignore

from .bridge_impl import MotionDetectorImpl
from .settings import RaspiGpioSensorSettings

LOGGER = logging.getLogger(__name__)


class RaspiGpioSensor(MotionDetectorImpl):
    """ Class for wrapping python motion sensor
    """

    def __init__(self, settings: RaspiGpioSensorSettings) -> None:
        LOGGER.info(f"Using motion sensor on pin {settings.gpio_pin_number}")
        self._motion_sensor = GPIOMotionSensor(pin=settings.gpio_pin_number,
                                               queue_len=settings.queue_length,
                                               sample_rate=settings.sample_wait,
                                               threshold=settings.threshold)
        self._motion_sensor.when_activated = self._when_activated
        self._motion_sensor.when_deactivated = self._when_deactivated
        if settings.led_gpio_pin_number > 0:
            self._led = LED(settings.led_gpio_pin_number)
        self._settings = settings

    def register_handler(self, handler: Callable[..., None]) -> None:
        LOGGER.debug("Registering motion_sensor callback")
        self._handler = handler

    def shutdown(self) -> None:
        LOGGER.info("Shutting down")
        # shutdown motion sensor thread and join
        self._motion_sensor.close()

    @property
    def id(self) -> int:
        return self._settings.gpio_pin_number

    def _when_activated(self) -> None:
        LOGGER.debug(f"Sensor activated, active time: {self._motion_sensor.active_time}")  # type: ignore
        self._led.on()
        if self._handler:
            self._handler()

    def _when_deactivated(self) -> None:
        LOGGER.debug(f"Sensor deactivated, inactive time: {self._motion_sensor.active_time}")  # type: ignore
        self._led.off()
