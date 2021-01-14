from contextlib import contextmanager
from sys import modules
from unittest import TestCase
from unittest.mock import Mock, MagicMock

from camguard.exceptions.input_error import InputError


class CamAdapterTest(TestCase):

    def setUp(self) -> None:
        """
        PiCamera is a black box in here, therefore we have to mock it
        """

        #setup mocks
        pi_camera_module = Mock()
        self.pi_camera = MagicMock(spec=contextmanager)
        pi_camera_module.PiCamera = self.pi_camera

        # mock import of the package
        modules['picamera'] = pi_camera_module

        from camguard.cam.cam_adapter import CamAdapter
        # create adapter with invalid record path
        self.sut = CamAdapter("")

        self.invalid_record_paths = ["/home/non/existing/file.ext", None]

    def test_should_raise_error_when_invalid_record_path(self):
        for path in self.invalid_record_paths:
            with self.subTest(record_path=path):
                # arrange
                self.sut.record_root_path = path
                self.pi_camera.capture_continuous = Mock()
                # act
                with self.assertRaises(InputError):
                    self.sut.record_picture()
                # assert
                self.pi_camera.capture_continuous.assert_not_called()

    def test_should_call_capture(self):
        # arrange
        record_path = "/home/"
        self.sut.record_root_path = record_path

        # act
        self.sut.record_picture()

        # assert
        found = False
        for name, arg, kwargs in self.pi_camera.mock_calls:
            if "capture_continuous" in name:
                found = True

        # check if
        self.assertTrue(found, "Check if 'capture_continuous' was called")
