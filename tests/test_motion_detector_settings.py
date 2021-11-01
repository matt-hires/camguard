
from typing import Any, Dict
from camguard.motion_detector_settings import DummyGpioSensorSettings, MotionDetectorSettings, RaspiGpioSensorSettings
from camguard.settings import ImplementationType
from unittest.case import TestCase
from unittest.mock import MagicMock, mock_open, patch


class MotionDetectorSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'motion_detector': {'implementation': 'dummy'}
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_set_correct_impl_type(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: MotionDetectorSettings = MotionDetectorSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)


class RaspiGpioSensorSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'motion_detector': {
                'implementation': 'raspi',
                'raspi_gpio_sensor': {
                    'gpio_pin_number': 23,
                    'notification_led_gpio_pin_number': 1,
                    'queue_length': 1,
                    'threshold': 2.0,
                    'sample_rate': 3.0
                }
            }
        }

    @staticmethod
    def mock_yaml_data_default() -> Dict[str, Any]:
        return {
            'motion_detector': {
                'implementation': 'raspi',
                'raspi_gpio_sensor': {
                    'gpio_pin_number': 23
                }
            }
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_implementation_type(self):
        # arrange
        data = self.mock_yaml_data_default()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: RaspiGpioSensorSettings = RaspiGpioSensorSettings.load_settings('.')

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
            settings: RaspiGpioSensorSettings = RaspiGpioSensorSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.RASPI, settings.impl_type)
        self.assertEqual(1, settings.led_gpio_pin_number)
        self.assertEqual(1, settings.queue_length)
        self.assertEqual(2.0, settings.threshold)
        self.assertEqual(3.0, settings.sample_rate)

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_default(self):
        # arrange
        data = self.mock_yaml_data_default()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: RaspiGpioSensorSettings = RaspiGpioSensorSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.RASPI, settings.impl_type)
        self.assertEqual(0, settings.led_gpio_pin_number)
        self.assertEqual(1, settings.queue_length)
        self.assertEqual(0.5, settings.threshold)
        self.assertEqual(10.0, settings.sample_rate)

class DummyGpioSensorSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'motion_detector': {
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
            settings: DummyGpioSensorSettings = DummyGpioSensorSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)
