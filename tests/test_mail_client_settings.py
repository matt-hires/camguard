
from typing import Any, Dict
from unittest.case import TestCase
from unittest.mock import MagicMock, mock_open, patch

from camguard.mail_client_settings import DummyMailClientSettings, GenericMailClientSettings, MailClientSettings
from camguard.settings import ImplementationType


class MailClientSettingsTest(TestCase):
    """this test includes testing Generic- and Dummy- MailClientSettings
    """

    @staticmethod
    def mock_yaml_data() -> Dict[str, Any]:
        return {
            'mail_client': {
                'implementation': 'dummy',
                'username': 'myUser',
                'password': 'myPw',
                'sender_mail': 'mail@sender.com',
                'receiver_mail': 'mail@receiver.com',
                'hostname': 'mail.myhost.com'
            }
        }

    @staticmethod
    def mock_yaml_data_default() -> Dict[str, Any]:
        return {
            'mail_client': {
                'username': 'myUser',
                'password': 'myPw',
                'sender_mail': 'mail@sender.com',
                'receiver_mail': 'mail@receiver.com',
                'hostname': 'mail.myhost.com'
            }
        }

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_settings(self):
        # arrange
        data = self.mock_yaml_data()
        safe_load_mock = MagicMock(return_value=data)

        # act
        for settings_cls in [MailClientSettings, GenericMailClientSettings, DummyMailClientSettings]:
            with self.subTest(settings_cls=settings_cls):
                with patch('camguard.settings.safe_load', safe_load_mock):
                    settings: MailClientSettings = settings_cls.load_settings('.')
                    # assert
                    self.assertEqual(ImplementationType.DUMMY, settings.impl_type)
                    self.assertEqual('myUser', settings.user)
                    self.assertEqual('myPw', settings.password)
                    self.assertEqual('mail@sender.com', settings.sender_mail)
                    self.assertEqual('mail@receiver.com', settings.receiver_mail)
                    self.assertEqual('mail.myhost.com', settings.hostname)

    @patch('camguard.settings.path.isfile', MagicMock(return_value=True))
    @patch('camguard.settings.open', mock_open())
    def test_should_parse_default(self):
        # arrange
        data = self.mock_yaml_data_default()
        safe_load_mock = MagicMock(return_value=data)

        # act
        for settings_cls in [MailClientSettings, GenericMailClientSettings, DummyMailClientSettings]:
            with self.subTest(settings_cls=settings_cls):
                with patch('camguard.settings.safe_load', safe_load_mock):
                    settings: MailClientSettings = MailClientSettings.load_settings('.')
                    # assert
                    self.assertEqual(ImplementationType.DEFAULT, settings.impl_type)
                    self.assertEqual('myUser', settings.user)
                    self.assertEqual('myPw', settings.password)
                    self.assertEqual('mail@sender.com', settings.sender_mail)
                    self.assertEqual('mail@receiver.com', settings.receiver_mail)
                    self.assertEqual('mail.myhost.com', settings.hostname)
