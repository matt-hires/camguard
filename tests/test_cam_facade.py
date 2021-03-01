import datetime
import os
import re
from contextlib import AbstractContextManager
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

from camguard.errors import ConfigurationError

HOME = "/home"
MODULES = "sys.modules"


class PiCameraFakeContextManager(AbstractContextManager):
    """
    fake object for the pi camera context manager
    otherwise i don't know how to track the methodcalls to capture_continuous
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class CamFacadeTest(TestCase):

    def setUp(self) -> None:
        """
        PiCamera is a black box in here, therefore we have to patch the modules
        """

        # setup mocks
        self.pi_camera_module = Mock()
        self.pi_camera_module.PiCamera = PiCameraFakeContextManager
        self.pi_camera_module.PiCamera.capture_continuous = Mock(return_value=["capture1.jpg", "capture2.jpg"])

        self.patcher = patch.dict(MODULES, picamera=self.pi_camera_module)
        self.patcher.start()

    @patch("os.path.isdir", MagicMock(spec=os.path.isdir, return_value=False))
    def test_should_raise_error_when_invalid_record_path(self):
        # arrange
        from camguard.cam_facade import CamFacade
        for path in [f"{HOME}/non/existing/file.ext", None]:
            with self.subTest(record_path=path):
                # arrange
                # create facade with invalid record path
                sut = CamFacade(path)
                sut.record_root_path = path

                # act
                with self.assertRaises(ConfigurationError):
                    sut.record_picture()
                # assert
                self.pi_camera_module.PiCamera.capture_continuous.assert_not_called()

    @patch("os.mkdir", MagicMock(spec=os.mkdir))
    def test_should_call_capture(self):
        # arrange
        from camguard.cam_facade import CamFacade
        sut = CamFacade(HOME)

        # act
        sut.record_picture()

        # assert
        self.pi_camera_module.PiCamera.capture_continuous.assert_called()

    @patch("os.path.isdir", MagicMock(spec=os.path.isdir, return_value=True))
    @patch("os.path.exists", MagicMock(spec=os.path.isdir, return_value=False))
    @patch.object(os, "mkdir")
    def test_should_create_date_folder(self, mkdir_method_mock: Mock):
        # arrange
        from camguard.cam_facade import CamFacade
        sut = CamFacade(HOME)

        date_str = datetime.date.today().strftime("%Y%m%d/")
        record_path = os.path.join(HOME, date_str)

        # act
        sut.record_picture()

        # assert
        mkdir_method_mock.assert_called_with(record_path)
        self.pi_camera_module.PiCamera.capture_continuous.assert_called_once()

        found = False
        for arg in self.pi_camera_module.PiCamera.capture_continuous.call_args:
            if arg and re.match(f"{record_path}.*", arg[0]):
                found = True

        self.assertTrue(found, "Check if record called for specific date folder name")

    @patch("os.path.isdir", MagicMock(spec=os.path.isdir, return_value=True))
    @patch("os.path.exists", MagicMock(spec=os.path.isdir, return_value=False))
    @patch("os.mkdir", MagicMock(spec=os.mkdir))
    def test_should_return_recorded_files(self):
        # arrange
        from camguard.cam_facade import CamFacade
        sut = CamFacade(HOME)

        # act
        return_val = sut.record_picture()

        # assert
        self.assertEqual(["capture1.jpg", "capture2.jpg"], return_val)

    @patch("os.path.isdir", MagicMock(spec=os.path.isdir, return_value=True))
    @patch("os.path.exists", MagicMock(spec=os.path.isdir, return_value=False))
    @patch.object(os, "mkdir")
    def test_should_shutdown(self, _):
        # arrange
        from camguard.cam_facade import CamFacade
        sut = CamFacade(HOME)

        # act
        sut.shutdown()
        sut.record_picture()

        # assert
        self.assertTrue(sut._shutdown)
        # should be called once
        self.pi_camera_module.PiCamera.capture_continuous.assert_called_once()

    def tearDown(self) -> None:
        self.patcher.stop()
