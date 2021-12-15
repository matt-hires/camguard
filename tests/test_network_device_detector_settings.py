
from typing import Any, Dict
from unittest.case import TestCase
from unittest.mock import MagicMock, mock_open, patch

from camguard.network_device_detector_settings import DummyNetworkDeviceDetectorSettings, NMapDeviceDetectorSettings, NetworkDeviceDetectorSettings
from camguard.settings import ImplementationType


class NetworkDeviceDetectorSettingsTest(TestCase):
    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'network_device_detector': {
                'implementation': 'dummy'
            }
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_dummy_mode(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: NetworkDeviceDetectorSettings = NetworkDeviceDetectorSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_dummy_mode_default(self):
        # arrange
        safe_load_mock = MagicMock(return_value={'network_device_detector': {}})

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: NetworkDeviceDetectorSettings = NetworkDeviceDetectorSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DEFAULT, settings.impl_type)


class NMapDeviceDetectorSettingsTest(TestCase):
    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'network_device_detector': {
                'nmap_device_detector': {
                    'ip_addr': ['1.2.3.4', '5.6.7.8'],
                    'interval_seconds': '2.0'
                }
            }
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_settings(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: NMapDeviceDetectorSettings = NMapDeviceDetectorSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DEFAULT, settings.impl_type)
        self.assertEqual(['1.2.3.4', '5.6.7.8'], settings.ip_addr)
        self.assertEqual('2.0', settings.interval_seconds)


class DummyDeviceDetectorSettingsTest(TestCase):
    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'network_device_detector': {
                'implementation': 'dummy'
            }
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_dummy_mode(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: DummyNetworkDeviceDetectorSettings = DummyNetworkDeviceDetectorSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)
