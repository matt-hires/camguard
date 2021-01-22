from sys import modules
from time import sleep
from unittest import TestCase
from unittest.mock import Mock, create_autospec

from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPin

from camguard.motionsensor.motionsensor_adapter import MotionSensorAdapter


class CamGuardTest(TestCase):

    def setUp(self):
        self.motion_sensor = Mock(spec=MotionSensorAdapter)

        # mock picamera package (see test_cam_adapter as well)
        self.picamera_mock = Mock()
        modules['picamera'] = self.picamera_mock

        # mock MotionSensor
        Device.pin_factory = MockFactory()

        from camguard.camguard import CamGuard
        self.gpio_pin = 13
        self.sut = CamGuard(self.gpio_pin, "")

        # mock camera
        from camguard.cam.cam_adapter import CamAdapter
        # Magic mock is necessary due to callback assignment
        self.sut.camera = create_autospec(spec=CamAdapter)

    def test_should_record_picture_on_motion(self):
        # arrange
        pin: MockPin = Device.pin_factory.pin(self.gpio_pin)
        # default is 1/10, waiting twice as long
        sample_wait_time_sec = (2 / 10)

        # act
        self.sut.guard()

        sleep(sample_wait_time_sec)
        pin.drive_high()
        sleep(sample_wait_time_sec)

        # assert
        self.sut.camera.record_picture.assert_called()

    def tearDown(self) -> None:
        Device.pin_factory.release_pins(self.sut.motion_sensor._motion_sensor, self.gpio_pin)
