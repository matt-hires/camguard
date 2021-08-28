
from typing import Any, Dict
from camguard.settings import ImplementationType
from camguard.motion_handler_settings import MotionHandlerSettings
from unittest.case import TestCase

from unittest.mock import patch, mock_open, MagicMock


class MotionHandlerSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'motion_handler': {'implementation': 'dummy'}
        }

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_set_correct_impl_type(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings = MotionHandlerSettings.load_settings(".")

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)
