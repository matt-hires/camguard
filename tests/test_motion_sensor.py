from time import sleep
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, call, create_autospec, patch

from gpiozero import Device, LED  # type: ignore
from gpiozero.pins.mock import MockFactory, MockPin  # type: ignore

from camguard.raspi_gpio_sensor import RaspiGpioSensor
from camguard.settings import RaspiGpioSensorSettings


class MotionSensorTest(TestCase):

    @patch("camguard.raspi_gpio_sensor.LED", autospec=LED)
    def setUp(self, led_mock: MagicMock):
        Device.pin_factory = MockFactory()
        self._sensor_settings_mock = create_autospec(spec=RaspiGpioSensorSettings, spec_set=True)
        type(self._sensor_settings_mock).gpio_pin_number = PropertyMock(return_value=13)
        type(self._sensor_settings_mock).queue_length = PropertyMock(return_value=1)
        type(self._sensor_settings_mock).sample_wait = PropertyMock(return_value=10.0)
        type(self._sensor_settings_mock).threshold = PropertyMock(return_value=0.5)
        type(self._sensor_settings_mock).led_gpio_pin_number = PropertyMock(return_value=16)
        self.sut = RaspiGpioSensor(self._sensor_settings_mock)
        self._led_mock = led_mock

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
        self._led_mock.assert_has_calls([call().on(), call().off()], any_order=True)
        # check led on calls 
        self.assertEquals(activations, sum(c == call().on() for c in self._led_mock.method_calls)) # type: ignore
        # check led off calls 
        self.assertEquals(activations, sum(c == call().off() for c in self._led_mock.method_calls)) # type: ignore

    def tearDown(self):
        Device.pin_factory.release_pins(self.sut._motion_sensor,  # type: ignore
                                        self._sensor_settings_mock.gpio_pin_number)
