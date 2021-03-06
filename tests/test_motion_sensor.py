from time import sleep
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, create_autospec

from gpiozero import Device  # type: ignore
from gpiozero.pins.mock import MockFactory, MockPin  # type: ignore

from camguard.raspi_gpio_sensor import RaspiGpioSensor
from camguard.settings import RaspiGpioSensorSettings


class MotionSensorTest(TestCase):
    def setUp(self):
        Device.pin_factory = MockFactory()
        self._sensor_settings_mock = create_autospec(spec=RaspiGpioSensorSettings, spec_set=True)
        type(self._sensor_settings_mock).gpio_pin_number = PropertyMock(return_value=13)
        self.sut = RaspiGpioSensor(self._sensor_settings_mock)

    def test_should_trigger_callback(self):
        """
        sleep calls in this test are necessary that motion sensor gets activated
        this is due to gpiozero.input_devices.SmoothedInputDevice.__init__  and
        the default sample wait time (1/10) configured in gpiozero/input_devices.py:612 (__init__)
        """
        # arrange
        mock_callback = MagicMock()
        # gpiozero needs __name__ attribute
        mock_callback.__name__ = "handler"
        pin: MockPin = Device.pin_factory.pin(self._sensor_settings_mock.gpio_pin_number)  # type: ignore
        # default is 1/10, waiting twice as long
        sample_wait_time_sec = (2 / 10)

        # act
        self.sut.register_handler(mock_callback)
        sleep(sample_wait_time_sec)
        activations = 2
        # activate sensor two times
        for _ in range(activations):
            pin.drive_high()
            sleep(sample_wait_time_sec)
            pin.drive_low()
            sleep(sample_wait_time_sec)

        # assert
        mock_callback.assert_called()
        self.assertEqual(activations, mock_callback.call_count)

    def tearDown(self):
        Device.pin_factory.release_pins(self.sut._motion_sensor, # type: ignore
                                        self._sensor_settings_mock.gpio_pin_number)
