from typing import Dict
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from camguard.exceptions import CamGuardError, ConfigurationError
from camguard.settings import (FileStorageSettings, ImplementationType,
                               MotionDetectorSettings, MotionHandlerSettings,
                               Settings)


class ImplementationTypeTest(TestCase):

    def test_should_parse_dummy(self):
        # arrange
        type = "dummy"

        # act
        parsed = ImplementationType.parse(type)

        # assert
        self.assertEqual(ImplementationType.DUMMY, parsed)

    def test_should_parse_raspi(self):
        # arrange
        type = "raspi"

        # act
        parsed = ImplementationType.parse(type)

        # assert
        self.assertEqual(ImplementationType.RASPI, parsed)

    def test_should_raise_configuration_error(self):
        for invalid_type in [None, "unknown_type"]:
            with self.subTest(type=invalid_type):
                # act / assert
                with self.assertRaises(ConfigurationError):
                    ImplementationType.parse(invalid_type)


class SettingsTest(TestCase):

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_load_and_parse(self):
        # arrange
        data = SettingsTest.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings = Settings.load_settings()

        # assert
        self.assertIsNotNone(settings)

    @patch("camguard.settings.path.isfile", MagicMock(return_value=False))
    def test_should_ignore_non_existant_file(self):
        # arrange
        open_mock = MagicMock()

        # act
        with patch("camguard.settings.open", mock_open(mock=open_mock)):
            Settings.load_settings()

        # assert
        open_mock.assert_not_called()

    @staticmethod
    def mock_yaml_data() -> Dict:
        return {
            'motion_handler': {'implementation': 'dummy'},
            'motion_detector': {'implementation': 'dummy'},
            'file_storage': {'implementation': 'dummy'}
        }


class MotionHandlerSettingsTest(TestCase):

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_set_correct_impl_type(self):
        # arrange
        data = SettingsTest.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings = MotionHandlerSettings.load_settings()

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)


class MotionDetectorSettingsTest(TestCase):

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_set_correct_impl_type(self):
        # arrange
        data = SettingsTest.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings = MotionDetectorSettings.load_settings()

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)


class FileStorageSettingsTest(TestCase):

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_set_correct_impl_type(self):
        # arrange
        data = SettingsTest.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings = FileStorageSettings.load_settings()

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)
