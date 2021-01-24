from contextlib import AbstractContextManager
from time import sleep
from unittest import TestCase
from unittest.mock import Mock, create_autospec, MagicMock, patch

from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPin

from camguard.camguard import CamGuard
from camguard.motionsensor.motionsensor_adapter import MotionSensorAdapter


class CamGuardTest(TestCase):

    def setUp(self):
        # setup mocks

        # cam
        pi_camera_module = Mock()
        pi_camera_module.PiCamera = Mock(spec=AbstractContextManager)

        self.patcher = patch.dict("sys.modules", picamera=pi_camera_module)
        self.patcher.start()

        # motion sensor
        self.gpio_pin = 13
        Device.pin_factory = MockFactory()

    def test_should_record_picture_on_motion(self):
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

    @patch("sys.exit")
    def test_should_shutdown(self, mock_exit: MagicMock):
        # arrange
        from camguard.cam.cam_adapter import CamAdapter

        self.sut = CamGuard(self.gpio_pin, "")
        self.sut.camera = create_autospec(spec=CamAdapter)
        self.sut.motion_sensor = create_autospec(spec=MotionSensorAdapter)
        self.sut.guard()

        # act
        self.sut.shutdown()

        # assert
        self.sut.camera.shutdown.assert_called()
        self.sut.motion_sensor.shutdown.assert_called()
        mock_exit.assert_called()

    def tearDown(self) -> None:
        self.patcher.stop()
        if hasattr(self.sut.motion_sensor, "_motion_sensor"):
            Device.pin_factory.release_pins(self.sut.motion_sensor._motion_sensor, self.gpio_pin)
