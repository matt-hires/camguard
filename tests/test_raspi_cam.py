import datetime
import re
from contextlib import AbstractContextManager
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch

from camguard.exceptions import ConfigurationError
from camguard.settings import RaspiCamSettings

MODULES = "sys.modules"


class RaspiCamFakeContextManager(AbstractContextManager):  # type: ignore
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

        self._raspi_cam_settings = create_autospec(spec=RaspiCamSettings, spec_set=True)
        self.patcher = patch.dict(MODULES, picamera=self.pi_camera_module)
        self.patcher.start()

    @patch("camguard.raspi_cam.os.path.isdir", MagicMock(return_value=False))
    def test_should_raise_error_when_invalid_record_path(self):
        # arrange
        from camguard.raspi_cam import RaspiCam
        for path in ["/non/existing/file.ext"]:
            with self.subTest(record_root_path=path):
                # arrange
                type(self._raspi_cam_settings).record_path = PropertyMock(return_value=path)
                sut = RaspiCam(self._raspi_cam_settings)

                # act
                with self.assertRaises(ConfigurationError):
                    sut.handle_motion()

                # assert
                self.pi_camera_module.PiCamera.capture_continuous.assert_not_called()  # type: ignore

    @patch("camguard.raspi_cam.os.mkdir", MagicMock())
    def test_should_call_capture(self):
        # arrange
        from camguard.raspi_cam import RaspiCam
        type(self._raspi_cam_settings).record_path = PropertyMock(return_value="/")
        sut = RaspiCam(self._raspi_cam_settings)

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
        type(self._raspi_cam_settings).record_path = PropertyMock(return_value=root)
        type(self._raspi_cam_settings).record_file_format = PropertyMock(
            return_value="{counter:03d}_{timestamp:%y%m%d_%H%M%S}_capture.jpg")
        sut = RaspiCam(self._raspi_cam_settings)

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
        type(self._raspi_cam_settings).record_path = PropertyMock(return_value="/")
        sut = RaspiCam(self._raspi_cam_settings)
        sut.shutdown()

        # act
        sut.handle_motion()

        # assert
        self.assertTrue(sut._shutdown)  # type: ignore
        self.pi_camera_module.PiCamera.capture_continuous.assert_not_called()  # type: ignore

    def tearDown(self):
        self.patcher.stop()
