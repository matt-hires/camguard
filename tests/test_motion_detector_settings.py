
from typing import Any, Dict
from camguard.motion_detector_settings import MotionDetectorSettings
from camguard.settings import ImplementationType
from unittest.case import TestCase
from unittest.mock import MagicMock, mock_open, patch


class MotionDetectorSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'motion_detector': {'implementation': 'dummy'}
        }

    @patch("camguard.settings.path.isfile", MagicMock(return_value=True))
    @patch("camguard.settings.open", mock_open())
    def test_should_set_correct_impl_type(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch("camguard.settings.safe_load", safe_load_mock):
            settings = MotionDetectorSettings.load_settings(".")

        # assert
        self.assertEqual(ImplementationType.DUMMY, settings.impl_type)
