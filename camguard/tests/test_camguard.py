from contextlib import contextmanager
from time import sleep
from unittest import TestCase
from unittest.mock import Mock, create_autospec, MagicMock, patch

from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPin

from camguard.camguard import CamGuard
from camguard.motionsensor.motionsensor_adapter import MotionSensorAdapter

MODULES = "sys.modules"


class CamGuardTest(TestCase):

    def setUp(self):
        # camera
        self.pi_camera_module = Mock()
        # Magic mock is necessary due to callback assignment
        self.pi_camera_module.PiCamera = MagicMock(spec=contextmanager)

        # motion sensor
        self.gpio_pin = 13
        self.motion_sensor = Mock(spec=MotionSensorAdapter)
        Device.pin_factory = MockFactory()

    def test_should_record_picture_on_motion(self):
        with patch.dict(MODULES, picamera=self.pi_camera_module):
            # arrange
            from camguard.cam.cam_adapter import CamAdapter

            self.sut = CamGuard(self.gpio_pin, "")
            self.sut.camera = create_autospec(spec=CamAdapter)

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
