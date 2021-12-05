from typing import Any, Dict
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from camguard.camguard_settings import CamguardSettings, ComponentsType
from camguard.exceptions import CamguardError, ConfigurationError


class ComponentsTypeTest(TestCase):

    def test_should_check_mandatory(self):
        # arrange
        components = [ComponentsType.MOTION_DETECTOR, ComponentsType.MAIL_CLIENT]

        # act
        missing = ComponentsType.check_mandatory(components)

        # assert
        self.assertEqual(1, len(missing))
        self.assertEqual(ComponentsType.MOTION_HANDLER.component_name, missing[0])

    def test_should_parse(self):
        # arrange / act
        for component in [ComponentsType.MOTION_HANDLER,
                          ComponentsType.MOTION_DETECTOR,
                          ComponentsType.FILE_STORAGE,
                          ComponentsType.MAIL_CLIENT,
                          ComponentsType.NETWORK_DEVICE_DETECTOR]:
            with self.subTest(component=component):
                # assert
                self.assertEqual(component, ComponentsType.parse(component.component_name))

    def test_should_raise_on_parse(self):
        # arrange
        not_implemented = "not_implemented"

        # act
        with self.assertRaises(CamguardError):
            ComponentsType.parse(not_implemented)

class CamguardSettingsTest(TestCase):

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'components': {
                'motion_handler',
                'motion_detector',
                'file_storage',
                'mail_client',
                'network_device_detector'
            }
        }

    @staticmethod
    def mock_yaml_data_missing_component() -> Dict[str, Any]:
        return {
            'components': {
                'file_storage',
                'mail_client',
                'network_device_detector'
            }
        }

    def setUp(self) -> None:
        self.__sut = CamguardSettings()

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_settings(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        with patch('camguard.settings.safe_load', safe_load_mock):
            settings: CamguardSettings = self.__sut.load_settings('.')

        # assert
        self.assertEqual(5, len(settings.components))
        self.assertIn(ComponentsType.MOTION_HANDLER, settings.components)
        self.assertIn(ComponentsType.MOTION_DETECTOR, settings.components)
        self.assertIn(ComponentsType.FILE_STORAGE, settings.components)
        self.assertIn(ComponentsType.MAIL_CLIENT, settings.components)
        self.assertIn(ComponentsType.NETWORK_DEVICE_DETECTOR, settings.components)

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_raise_on_parse_settings(self):
        # arrange
        data = self.mock_yaml_data_missing_component()
        safe_load_mock = MagicMock(return_value=data)

        # act / assert
        with patch('camguard.settings.safe_load', safe_load_mock),\
            self.assertRaises(ConfigurationError):
            self.__sut.load_settings('.')


