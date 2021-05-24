import datetime
import re
from contextlib import AbstractContextManager
from unittest import TestCase
from unittest.mock import MagicMock, patch

from camguard.exceptions import ConfigurationError

MODULES = "sys.modules"


class RaspiCamFakeContextManager(AbstractContextManager): # type: ignore
    """
    fake object for the pi camera context manager
    otherwise i don't know how to track the methodcalls to capture_continuous
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        return False


class RaspiCamTest(TestCase):

    def setUp(self):
        """
        PiCamera is a black box in here, therefore we have to patch the modules
        """

        # setup mocks
        self.pi_camera_module = MagicMock()
        self.pi_camera_module.PiCamera = RaspiCamFakeContextManager
        setattr(self.pi_camera_module.PiCamera, "capture_continuous",  # type: ignore
                MagicMock(return_value=["capture1.jpg", "capture2.jpg"]))

        self.patcher = patch.dict(MODULES, picamera=self.pi_camera_module)
        self.patcher.start()

    @patch("camguard.raspi_cam.os.path.isdir", MagicMock(return_value=False))
    def test_should_raise_error_when_invalid_record_path(self):
        # arrange
        from camguard.raspi_cam import RaspiCam
        for path in ["/non/existing/file.ext"]:
            with self.subTest(record_root_path=path):
                # arrange
                sut = RaspiCam(path)

                # act
                with self.assertRaises(ConfigurationError):
                    sut.handle_motion()

                # assert
                self.pi_camera_module.PiCamera.capture_continuous.assert_not_called()  # type: ignore

    @patch("camguard.raspi_cam.os.mkdir", MagicMock())
    def test_should_call_capture(self):
        # arrange
        from camguard.raspi_cam import RaspiCam
        sut = RaspiCam("/")

        # act
        sut.handle_motion()

        # assert
        self.pi_camera_module.PiCamera.capture_continuous.assert_called()  # type: ignore

    @patch("camguard.raspi_cam.os.path.isdir", MagicMock(return_value=True))
    @patch("camguard.raspi_cam.os.path.exists", MagicMock(return_value=False))
    @patch("camguard.raspi_cam.os.mkdir")
    def test_should_create_date_folder(self, mkdir_method_mock: MagicMock):
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
        self.pi_camera_module.PiCamera.capture_continuous.assert_called_once()  # type: ignore

        found = False
        for arg in self.pi_camera_module.PiCamera.capture_continuous.call_args:  # type: ignore
            if arg and re.match(f"{record_path}.*", arg[0]):  # type: ignore
                found = True

        self.assertTrue(found, "Check if record called for specific date folder name")

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
        self.assertTrue(sut._shutdown)  # type: ignore
        self.pi_camera_module.PiCamera.capture_continuous.assert_not_called()  # type: ignore

    def tearDown(self):
        self.patcher.stop()
