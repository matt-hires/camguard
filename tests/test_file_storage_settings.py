
from typing import Any, Dict
from unittest.case import TestCase
from unittest.mock import MagicMock, mock_open, patch

from camguard.file_storage_settings import FileStorageSettings


class FileStorageSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'file_storage1': {'dummy_implementation': True}
        }

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_set_correct_impl_type(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings = FileStorageSettings.load_settings(".")

        # assert
        self.assertEqual(False, settings.dummy_impl)
