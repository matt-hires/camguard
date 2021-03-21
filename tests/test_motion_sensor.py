from time import sleep
from unittest import TestCase
from unittest.mock import create_autospec

from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPin
from camguard.motion import MotionHandler

from camguard.motion_sensor import MotionSensor

class MotionSensorTest(TestCase):
    def setUp(self):
        Device.pin_factory = MockFactory()
        self.gpio_pin = 13
        self.sut = MotionSensor(self.gpio_pin)

    def test_should_trigger_callback(self):
        """
        sleep calls in this test are necessary that motion sensor gets activated
        this is due to gpiozero.input_devices.SmoothedInputDevice.__init__  and
        the default sample wait time (1/10) configured in gpiozero/input_devices.py:612 (__init__)
        """
        # arrange
        mock_callback = create_autospec(spec=MotionHandler)
        pin: MockPin = Device.pin_factory.pin(self.gpio_pin)
        # default is 1/10, waiting twice as long
        sample_wait_time_sec = (2 / 10)

        # act
        self.sut.detect_motion(mock_callback)
        sleep(sample_wait_time_sec)
        activations = 2
        # activate sensor two times
        for _ in range(activations):
            pin.drive_high()
            sleep(sample_wait_time_sec)
            pin.drive_low()
            sleep(sample_wait_time_sec)

        # assert
        mock_callback.on_motion.assert_called()
        self.assertEqual(activations, mock_callback.on_motion.call_count)

    def tearDown(self):
        Device.pin_factory.release_pins(self.sut._motion_sensor, self.gpio_pin)
