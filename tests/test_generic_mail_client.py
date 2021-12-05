from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch
from camguard.generic_mail_client import GenericMailClient
from camguard.mail_client_settings import GenericMailClientSettings


class GenericMailClientTest(TestCase):

    def setUp(self) -> None:
        self.__settings_mock = create_autospec(spec=GenericMailClientSettings, spec_set=True)
        type(self.__settings_mock).sender_mail = PropertyMock(return_value="sender@mail.com")
        type(self.__settings_mock).receiver_mail = PropertyMock(return_value="sender@mail.com")
        type(self.__settings_mock).user = PropertyMock(return_value="myUser")
        type(self.__settings_mock).password = PropertyMock(return_value="myPassword")

        self.__sut = GenericMailClient(self.__settings_mock)

    @patch('camguard.generic_mail_client.Client')
    def test_should_send_mail(self, client_mock: MagicMock):
        # arrange
        files = ['file1.jpeg', 'file2.jpeg']
        create_msg_mock = MagicMock()
        self.__sut.__setattr__(f"_{type(self.__sut)}__create_msg", create_msg_mock)

        # act
        self.__sut.send_mail(files)

        # assert
        client_mock().__enter__().starttls.assert_called()
        client_mock().__enter__().login.assert_called_with(self.__settings_mock.user, self.__settings_mock.password)
        client_mock().__enter__().send_message.assert_called()
