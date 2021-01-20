import datetime
import os
import re
from contextlib import contextmanager
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

from camguard.exceptions.input_error import InputError

HOME = "/home"
MODULES = "sys.modules"


class CamAdapterTest(TestCase):

    def setUp(self) -> None:
        """
        PiCamera is a black box in here, therefore we have to mock it
        """

        # setup mocks
        self.pi_camera_module = Mock()
        self.pi_camera_module.PiCamera = MagicMock(spec=contextmanager)

    @patch("os.path.isdir", MagicMock(spec=os.path.isdir, return_value=False))
    def test_should_raise_error_when_invalid_record_path(self):
        # arrange
        self.pi_camera_module.PiCamera.capture_continuous = Mock()

        with patch.dict(MODULES, picamera=self.pi_camera_module):
            from camguard.cam.cam_adapter import CamAdapter
            for path in [f"{HOME}/non/existing/file.ext", None]:
                with self.subTest(record_path=path):
                    # arrange
                    # create adapter with invalid record path
                    sut = CamAdapter(path)
                    sut.record_root_path = path

                    # act
                    with self.assertRaises(InputError):
                        sut.record_picture()
                    # assert
                    self.pi_camera_module.PiCamera.capture_continuous.assert_not_called()

    @patch("os.mkdir", MagicMock(spec=os.mkdir))
    def test_should_call_capture(self):
        # arrange
        with patch.dict(MODULES, picamera=self.pi_camera_module):
            from camguard.cam.cam_adapter import CamAdapter
            sut = CamAdapter(HOME)

            # act
            sut.record_picture()

            # assert
            found = False
            for name, arg, kwargs in self.pi_camera_module.PiCamera.mock_calls:
                if "capture_continuous" in name:
                    found = True

            self.assertTrue(found, "Check if 'capture_continuous' was called")

    @patch("os.path.isdir", MagicMock(spec=os.path.isdir, return_value=True))
    @patch("os.path.exists", MagicMock(spec=os.path.isdir, return_value=False))
    @patch.object(os, "mkdir")
    def test_should_create_date_folder(self, mkdir_method_mock: Mock):
        # arrange
        with patch.dict(MODULES, picamera=self.pi_camera_module):
            from camguard.cam.cam_adapter import CamAdapter
            sut = CamAdapter(HOME)
            date_str = datetime.date.today().strftime("%Y%m%d/")
            record_path = os.path.join(HOME, date_str)

            # act
            sut.record_picture()

            # assert
            mkdir_method_mock.assert_called_with(record_path)

            found = False
            for name, arg, kwargs in self.pi_camera_module.PiCamera.mock_calls:
                if "capture_continuous" in name and arg and \
                        re.match(f"{record_path}.*", arg[0]):
                    found = True

            self.assertTrue(found, "Check if record called for specific date folder name")

    def tearDown(self) -> None:
        self.pi_camera_module.reset_mock()

