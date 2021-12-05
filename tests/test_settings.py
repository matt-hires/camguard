from typing import Any, Dict
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from camguard.exceptions import ConfigurationError
from camguard.settings import (ImplementationType, Settings)


class ImplementationTypeTest(TestCase):

    def test_should_parse_dummy(self):
        # arrange - act
        parsed = ImplementationType.parse(ImplementationType.DUMMY.value)

        # assert
        self.assertEqual(ImplementationType.DUMMY, parsed)

    def test_should_parse_raspi(self):
        # arrange- act
        parsed = ImplementationType.parse(ImplementationType.RASPI.value)

        # assert
        self.assertEqual(ImplementationType.RASPI, parsed)

    def test_should_parse_default(self):
        # arrange- act
        parsed = ImplementationType.parse(ImplementationType.DEFAULT.value)

        # assert
        self.assertEqual(ImplementationType.DEFAULT, parsed)

    def test_should_raise_configuration_error(self):
        # act / assert
        with self.assertRaises(ConfigurationError):
            ImplementationType.parse('unknown_type')


class SettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'key1': {'subkey1': 'value1'},
            'key2': {'subkey2': 'value2'},
            'key3': {'subkey3': 'value3'}
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_load_and_parse(self):
        # arrange
        data = self.mock_yaml_data()

        # act
        with patch('camguard.settings.safe_load', MagicMock(return_value=data)):
            settings = Settings.load_settings('.')

        # assert
        self.assertIsNotNone(settings)

    @patch('camguard.settings.path.isfile', MagicMock(return_value=False))
    def test_should_raise_error_when_non_existant_file(self):
        # arrange
        open_mock = MagicMock()

        # act
        with patch('camguard.settings.open', mock_open(mock=open_mock)), \
                self.assertRaises(ConfigurationError):
            Settings.load_settings('.')

        # assert
        open_mock.assert_not_called()

    def test_should_get_setting_from_key(self):
        # arrange
        data = self.mock_yaml_data()

        # act
        setting = Settings.get_setting_from_key(setting_key='key1.subkey1', settings=data)

        # assert
        self.assertEqual('value1', setting)

    def test_should_get_default_setting_from_key(self):
        # arrange
        data = self.mock_yaml_data()

        # act
        setting = Settings.get_setting_from_key(setting_key='key1.subkey2',
                                                settings=data,
                                                default=False)  # use a falsy default here

        # assert
        self.assertEqual(False, setting)

    def test_should_raise_when_get_setting_from_non_existing_subkey(self):
        # arrange
        data = self.mock_yaml_data()
        key = 'motion_handler.implementation.raspi_cam'

        # act
        with self.assertRaises(ConfigurationError) as config_error:
            Settings.get_setting_from_key(setting_key=key, settings=data)
            # assert
            self.assertTrue(f'settings key not found: {key}' in config_error.message)  # type: ignore

    def test_should_raise_when_get_setting_from_non_existing_rootkey(self):
        # arrange
        data = self.mock_yaml_data()
        key = 'test'

        # act
        with self.assertRaises(ConfigurationError) as config_error:
            Settings.get_setting_from_key(setting_key=key, settings=data)
            # assert
            self.assertTrue(f'settings key not found: {key}' in config_error.message)  # type: ignore
