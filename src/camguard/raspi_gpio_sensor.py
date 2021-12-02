import logging
from typing import Callable

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
        self._motion_sensor = GPIOMotionSensor(pin=settings.gpio_pin_number,
                                               queue_len=settings.queue_length,
                                               sample_rate=settings.sample_rate,
                                               threshold=settings.threshold)

        self._settings = settings
        self._motion_sensor.when_activated = self._when_activated
        self._motion_sensor.when_deactivated = self._when_deactivated

        if settings.led_gpio_pin_number > 0:
            self._led = LED(settings.led_gpio_pin_number)

        # store activation status
        self._activated = False 

    def register_handler(self, handler: Callable[..., None]) -> None:
        LOGGER.debug("Registering motion_sensor callback")
        # skipcq: PYL-W0201
        self._handler = handler

    def shutdown(self) -> None:
        LOGGER.info("Shutting down")
        # shutdown motion sensor thread and join
        self._motion_sensor.close()

    @property
    def id(self) -> int:
        return self._settings.gpio_pin_number

    def _when_activated(self) -> None:
        if self.disabled:
            LOGGER.debug("Sensor disabled, activation signal ignored")

        self._activated = True
        LOGGER.debug(f"Sensor activated, active time: {self._motion_sensor.active_time}")  # type: ignore

        if hasattr(self, "_led"):
            self._led.on()

        if hasattr(self, "_handler"):
            self._handler()

    def _when_deactivated(self) -> None:
        # when disabled, still check activation flag - in case of disable between activation cycle
        if self.disabled and not self._activated:
            LOGGER.debug("Sensor disabled, deactivation signal ignored")

        self._activated = False
        LOGGER.debug(f"Sensor deactivated, inactive time: {self._motion_sensor.active_time}")  # type: ignore
        if hasattr(self, "_led"):
            self._led.off()
