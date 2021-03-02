from contextlib import AbstractContextManager
from time import sleep
from unittest import TestCase
from unittest.mock import Mock, create_autospec, MagicMock, patch

from gpiozero import Device
from gpiozero.pins.mock import MockFactory, MockPin

from camguard.motionsensor_facade import MotionSensorFacade


class CamGuardTest(TestCase):

    @patch("camguard.gdrive_facade.GDriveFacade")
    def setUp(self, _):
        # setup mocks

        # cam
        pi_camera_module = Mock()
        pi_camera_module.PiCamera = MagicMock(spec=AbstractContextManager)

        self.patcher = patch.dict("sys.modules", picamera=pi_camera_module)
        self.patcher.start()

        # motion sensor
        self.gpio_pin = 13
        Device.pin_factory = MockFactory()

        from camguard.camguard import CamGuard
        self.sut = CamGuard(self.gpio_pin, "", True)
        from camguard.cam_facade import CamFacade
        self.sut.camera = create_autospec(spec=CamFacade)

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
        self.sut.camera.record_picture.assert_called_once()

    def test_should_shutdown(self):
        # arrange
        self.sut.motion_sensor = create_autospec(spec=MotionSensorFacade)
        self.sut.guard()

        # act
        self.sut.shutdown()

        # assert
        self.sut.camera.shutdown.assert_called_once()
        self.sut.motion_sensor.shutdown.assert_called_once()

    def test_should_authenticate_when_gdrive_upload(self):
        # arrange

        # act
        self.sut.guard()

        # assert
        self.sut.gdrive.authenticate.assert_called_once()

    def test_should_upload_recorded_files_when_gdrive_upload(self):
        # arrange
        files = ["capture1.jpg", "capture2.jpg"]
        self.sut.camera.record_picture.return_value = files

        pin: MockPin = Device.pin_factory.pin(self.gpio_pin)
        # default is 1/10, waiting twice as long
        sample_wait_time_sec = (2 / 10)

        # act
        self.sut.guard()

        sleep(sample_wait_time_sec)
        pin.drive_high()
        sleep(sample_wait_time_sec)

        # assert
        self.sut.camera.record_picture.assert_called_once()
        self.sut.gdrive.upload.assert_called_once_with(files)

    def tearDown(self) -> None:
        self.patcher.stop()
        if hasattr(self.sut.motion_sensor, "_motion_sensor"):
            Device.pin_factory.release_pins(self.sut.motion_sensor._motion_sensor, self.gpio_pin)
