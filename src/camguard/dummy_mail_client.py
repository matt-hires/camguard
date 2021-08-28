import logging
import ssl
from email.message import EmailMessage
from smtplib import SMTP as Client, SMTPConnectError
from typing import ClassVar, List

from camguard.bridge_impl import MailClientImpl
from camguard.certs import MAIL_CERT
from camguard.dummy_mail_server import DummyMailServer
from camguard.mail_client_settings import DummyMailClientSettings

LOGGER = logging.getLogger(__name__)


class DummyMailClient(MailClientImpl):
    """dummy implementation for mail notification
    """
    _PORT: ClassVar[int] = 8025
    _MAIL_MSG: ClassVar[str] = "Notification test mail: Recording was triggered, and following files recorded: {files}"

    def __init__(self, settings: DummyMailClientSettings) -> None:
        self._settings = settings
        self._ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self._ssl_context.load_verify_locations(MAIL_CERT)
        self._ssl_context.check_hostname = False

    def send_mail(self, files: List[str]) -> None:
        LOGGER.info(f"Sending mail with: {files}")
        sender = self._settings.sender_mail
        receiver = self._settings.receiver_mail

        try:
            # implicitly start mail server for dummy delivery
            # performance should not be an issue in this context
            with DummyMailServer(user=self._settings.user,
                                 password=self._settings.password,
                                 port=DummyMailClient._PORT), \
                    Client(host=self._settings.hostname, port=DummyMailClient._PORT) as client:

                client.starttls()
                client.login(self._settings.user, self._settings.password)
                client.send_message(self._create_msg(sender, receiver, files))

        except (TimeoutError, RuntimeError) as server_err:
            LOGGER.error(f"Error while start mail server: {self._settings.hostname}:{DummyMailClient._PORT}",
                         exc_info=server_err)
        except (SMTPConnectError, OSError) as client_err:
            LOGGER.error(f"Error while connecting to mail server: {self._settings.hostname}:{DummyMailClient._PORT}",
                         exc_info=client_err)

    def _create_msg(self, sender: str, receiver: str, files: List[str]) -> EmailMessage:
        msg: EmailMessage = EmailMessage()
        msg.add_header("Subject", self.__class__.__name__ + " test mail")
        msg.add_header("From", sender)
        msg.add_header("To", receiver)
        msg.set_content(DummyMailClient._MAIL_MSG.format(files=files))

        return msg
