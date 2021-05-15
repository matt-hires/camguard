import datetime
import os
import re
from contextlib import AbstractContextManager
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

from camguard.exceptions import ConfigurationError
from camguard.bridge import MotionHandler

MODULES = "sys.modules"


class RaspiCamFakeContextManager(AbstractContextManager):
    """
    fake object for the pi camera context manager
    otherwise i don't know how to track the methodcalls to capture_continuous
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class RaspiCamTest(TestCase):

    def setUp(self):
        """
        PiCamera is a black box in here, therefore we have to patch the modules
        """

        # setup mocks
        self.pi_camera_module = MagicMock()
        self.pi_camera_module.PiCamera = RaspiCamFakeContextManager
        self.pi_camera_module.PiCamera.capture_continuous = MagicMock(
            return_value=["capture1.jpg", "capture2.jpg"])

        self.patcher = patch.dict(MODULES, picamera=self.pi_camera_module)
        self.patcher.start()

    @patch("camguard.raspi_cam.os.path.isdir", MagicMock(return_value=False))
    def test_should_raise_error_when_invalid_record_path(self):
        # arrange
        from camguard.raspi_cam import RaspiCam
        for path in [f"/non/existing/file.ext", None]:
            with self.subTest(record_path=path):
                # arrange
                sut = RaspiCam(path)

                # act
                with self.assertRaises(ConfigurationError):
                    sut.handle_motion()

                # assert
                self.pi_camera_module.PiCamera.capture_continuous.assert_not_called()

    @patch("camguard.raspi_cam.os.mkdir", MagicMock())
    def test_should_call_capture(self):
        # arrange
        from camguard.raspi_cam import RaspiCam
        sut = RaspiCam("/")

        # act
        sut.handle_motion()

        # assert
        self.pi_camera_module.PiCamera.capture_continuous.assert_called()

    @patch("camguard.raspi_cam.os.path.isdir", MagicMock(return_value=True))
    @patch("camguard.raspi_cam.os.path.exists", MagicMock(return_value=False))
    @patch("camguard.raspi_cam.os.mkdir")
    def test_should_create_date_folder(self, mkdir_method_mock):
        # arrange
        from camguard.raspi_cam import RaspiCam
        root = "/"
        sut = RaspiCam(root)

        date_str = datetime.date.today().strftime("%Y%m%d")
        record_path = f"{root}{date_str}/"

        # act
        sut.handle_motion()

        # assert
        mkdir_method_mock.assert_called_with(record_path)
        self.pi_camera_module.PiCamera.capture_continuous.assert_called_once()

        found = False
        for arg in self.pi_camera_module.PiCamera.capture_continuous.call_args:
            if arg and re.match(f"{record_path}.*", arg[0]):
                found = True

        self.assertTrue(found, "Check if record called for specific date folder name")

    @patch("camguard.raspi_cam.os.path.isdir", MagicMock(return_value=True))
    @patch("camguard.raspi_cam.os.path.exists", MagicMock(return_value=False))
    @patch("camguard.raspi_cam.os.mkdir", MagicMock())
    def test_should_trigger_motion_finished(self):
        # arrange
        from camguard.raspi_cam import RaspiCam
        sut: MotionHandler = RaspiCam("/")
        sut.after_handling = MagicMock()

        # act
        sut.handle_motion()

        # assert
        sut.after_handling.assert_called_once()

    @patch("camguard.raspi_cam.os.path.isdir", MagicMock(return_value=True))
    @patch("camguard.raspi_cam.os.path.exists", MagicMock(return_value=False))
    @patch("camguard.raspi_cam.os.mkdir", MagicMock())
    def test_should_shutdown(self):
        # arrange
        from camguard.raspi_cam import RaspiCam
        sut = RaspiCam("/")
        sut.shutdown()

        # act
        sut.handle_motion()

        # assert
        self.assertTrue(sut._shutdown)
        self.pi_camera_module.PiCamera.capture_continuous.assert_not_called()

    def tearDown(self):
        self.patcher.stop()
