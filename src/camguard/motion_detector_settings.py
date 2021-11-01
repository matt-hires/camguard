from typing import Any, ClassVar, Dict

from camguard.settings import ImplementationType, Settings


class MotionDetectorSettings(Settings):
    """Specialized motion detector settings class
    """
    _IMPL: ClassVar[str] = "implementation"
    _KEY: ClassVar[str] = "motion_detector"

    @property
    def impl_type(self) -> ImplementationType:
        return self._impl_type

    @impl_type.setter
    def impl_type(self, value: ImplementationType):
        self._impl_type = value

    def _parse_data(self, data: Dict[str, Any]):
        self.impl_type = ImplementationType.parse(super().get_setting_from_key(
            setting_key=f"{MotionDetectorSettings._KEY}.{MotionDetectorSettings._IMPL}",
            settings=data,
            default=ImplementationType.RASPI))


class RaspiGpioSensorSettings(MotionDetectorSettings):
    """Specialized motion detector settings for raspi gpio sensor
    """
    _KEY: ClassVar[str] = "raspi_gpio_sensor"
    _GPIO_PIN_NUMBER: ClassVar[str] = "gpio_pin_number"
    _NOTIFICATION_LED_GPIO_PIN_NUMBER: ClassVar[str] = "notification_led_gpio_pin_number"
    _QUEUE_LENGTH: ClassVar[str] = "queue_length"
    _THRESHOLD: ClassVar[str] = "threshold"
    _SAMPLE_RATE: ClassVar[str] = "sample_rate"

    @property
    def gpio_pin_number(self) -> int:
        return self._gpio_pin_number

    @gpio_pin_number.setter
    def gpio_pin_number(self, value: int) -> None:
        self._gpio_pin_number = value

    @property
    def led_gpio_pin_number(self) -> int:
        return self._led_gpio_pin_number

    @led_gpio_pin_number.setter
    def led_gpio_pin_number(self, value: int) -> None:
        self._led_gpio_pin_number = value

    @property
    def sample_rate(self) -> float:
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, value: float) -> None:
        self._sample_rate = value

    @property
    def queue_length(self) -> int:
        return self._queue_length

    @queue_length.setter
    def queue_length(self, value: int) -> None:
        self._queue_length = value

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        self._threshold = value

    def _parse_data(self, data: Dict[str, Any]):
        """parse settings data for raspi gpio sensor settings
        take care: in here self._KEY is used for key, this can be a different value than RaspiGpioSensorSettings._KEY,
        especially when using DummyGpioSensorSettings where this value will be overwritten
        """
        super()._parse_data(data)

        self.gpio_pin_number = super().get_setting_from_key(
            setting_key=f"{MotionDetectorSettings._KEY}.{self._KEY}.{RaspiGpioSensorSettings._GPIO_PIN_NUMBER}",
            settings=data
        )

        self.led_gpio_pin_number = super().get_setting_from_key(
            setting_key=f"{MotionDetectorSettings._KEY}.{self._KEY}."
            f"{RaspiGpioSensorSettings._NOTIFICATION_LED_GPIO_PIN_NUMBER}",
            settings=data,
            default=0  # 0 -> disable the notification led by default
        )

        self.sample_rate = super().get_setting_from_key(
            setting_key=f"{MotionDetectorSettings._KEY}.{self._KEY}.{RaspiGpioSensorSettings._SAMPLE_RATE}",
            settings=data,
            default=10.0
        )

        self.queue_length = super().get_setting_from_key(
            setting_key=f"{MotionDetectorSettings._KEY}.{self._KEY}.{RaspiGpioSensorSettings._QUEUE_LENGTH}",
            settings=data,
            default=1
        )

        self.threshold = super().get_setting_from_key(
            setting_key=f"{MotionDetectorSettings._KEY}.{self._KEY}.{RaspiGpioSensorSettings._THRESHOLD}",
            settings=data,
            default=0.5
        )


class DummyGpioSensorSettings(MotionDetectorSettings):
    """specialized motion detector settings for dummy gpio sensor
    """
    _KEY: ClassVar[str] = "dummy_gpio_sensor"
