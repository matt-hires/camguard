
from typing import Any, Dict
from camguard.settings import ImplementationType
from camguard.motion_handler_settings import DummyCamSettings, MotionHandlerSettings, RaspiCamSettings
from unittest.case import TestCase

from unittest.mock import patch, mock_open, MagicMock


class MotionHandlerSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'motion_handler': {'implementation': 'dummy'}
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_set_correct_impl_type(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings = MotionHandlerSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)


class RaspiCamSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'motion_handler': {
                'implementation': 'raspi',
                'raspi_cam': {
                    'record_path': '$HOME/.camguard/test',
                    'record_count': 20,
                    'record_interval_seconds': 3.0,
                    'record_file_format': '{counter:03d}_test_format_capture.jpg'
                }
            }
        }

    @staticmethod
    def mock_yaml_data_default() -> Dict[str, Any]:
        return {
            'motion_handler': {'implementation': 'raspi'}
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_implementation_type(self):
        # arrange
        data = self.mock_yaml_data_default()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: MotionHandlerSettings = MotionHandlerSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.RASPI, settings.impl_type)

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_settings(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: RaspiCamSettings = RaspiCamSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.RASPI, settings.impl_type)
        self.assertEqual(20, settings.record_count)
        self.assertEqual(3.0, settings.record_interval_sec)
        self.assertEqual('{counter:03d}_test_format_capture.jpg', settings.record_file_format)
        self.assertEqual('$HOME/.camguard/test', settings.record_path)

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_default(self):
        # arrange
        data = self.mock_yaml_data_default()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: RaspiCamSettings = RaspiCamSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.RASPI, settings.impl_type)
        self.assertEqual(15, settings.record_count)
        self.assertEqual(1.0, settings.record_interval_sec)
        self.assertEqual('{counter:03d}_{timestamp:%y%m%d_%H%M%S%f}_capture.jpg', settings.record_file_format)
        self.assertEqual('$HOME/.camguard/records', settings.record_path)


class DummyCamSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'motion_handler': {
                'implementation': 'dummy'
            }
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_implementation_type(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: DummyCamSettings = DummyCamSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)
