
from typing import Any, Dict
from unittest.case import TestCase
from unittest.mock import MagicMock, mock_open, patch

from camguard.file_storage_settings import DummyGDriveStorageSettings, FileStorageSettings, GDriveStorageSettings
from camguard.settings import ImplementationType


class FileStorageSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'file_storage': {'implementation': 'dummy'}
        }

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_parse_dummy_implementation(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings: FileStorageSettings = FileStorageSettings.load_settings(".")

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_parse_dummy_implementation_default(self):
        # arrange
        safe_load_mock = MagicMock(return_value={'file_storage': {}})

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings: FileStorageSettings = FileStorageSettings.load_settings(".")

        # assert
        self.assertEqual(ImplementationType.DEFAULT, settings.impl_type)


class GDriveStorageSettingsTest(TestCase):
    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'file_storage': {
                'gdrive_storage': {
                    'upload_folder_name': 'test',
                    'oauth_token_path': './testTokenPath',
                    'oauth_credentials_path': './testCredentialsPath'
                }
            }
        }

    @staticmethod
    def mock_yaml_data_default() -> Dict[str, Any]:
        return {
            'file_storage': {
                'gdrive_storage': {
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
            settings: GDriveStorageSettings = GDriveStorageSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DEFAULT, settings.impl_type)
        self.assertEqual('test', settings.upload_folder_name)
        self.assertEqual('./testTokenPath', settings.oauth_token_path)
        self.assertEqual('./testCredentialsPath', settings.oauth_credentials_path)

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_settings_default(self):
        # arrange
        data = self.mock_yaml_data_default()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: GDriveStorageSettings = GDriveStorageSettings.load_settings('.')

        # assert
        self.assertEqual(ImplementationType.DEFAULT, settings.impl_type)
        self.assertEqual('Camguard', settings.upload_folder_name)
        self.assertEqual('.', settings.oauth_token_path)
        self.assertEqual('.', settings.oauth_credentials_path)


class DummyGDriveStorageSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'file_storage': {
                'dummy_implementation': True
            }
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_dummy_implementation(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings: DummyGDriveStorageSettings = DummyGDriveStorageSettings.load_settings(".")

        # assert
        self.assertTrue(settings.impl_type)
