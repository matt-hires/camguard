
import logging
import ssl
from email.message import EmailMessage
from smtplib import SMTP as Client
from smtplib import SMTPConnectError
from typing import ClassVar, List

from camguard.bridge_impl import MailClientImpl
from camguard.settings import GenericMailClientSettings

LOGGER = logging.getLogger(__name__)


class GenericMailClient(MailClientImpl):
    _PORT: ClassVar[int] = 587  # for starttls
    _MAIL_MSG: ClassVar[str] = "Camguard motion triggered, files where recorded and uploaded: {files}"
    _MAIL_SUBJECT: ClassVar[str] = "Camguard motion triggered"

    def __init__(self, settings: GenericMailClientSettings) -> None:
        self._settings = settings
        self._ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

    def send_mail(self, files: List[str]) -> None:
        LOGGER.info(f"Sending mail with: {files}")
        sender = self._settings.sender_mail
        receiver = self._settings.receiver_mail

        try:
            with Client(host=self._settings.hostname, port=GenericMailClient._PORT) as client:
                client.starttls()
                client.login(self._settings.user, self._settings.password)
                client.send_message(self._create_msg(sender, receiver, files))
        except (SMTPConnectError, OSError) as client_err:
            LOGGER.error(f"Error while connecting to mail server: {self._settings.hostname}:{GenericMailClient._PORT}",
                         exc_info=client_err)


    def _create_msg(self, sender: str, receiver: str, files: List[str]) -> EmailMessage:
        msg: EmailMessage = EmailMessage()
        msg.add_header("Subject", GenericMailClient._MAIL_MSG)
        msg.add_header("From", sender)
        msg.add_header("To", receiver)
        msg.set_content(GenericMailClient._MAIL_MSG.format(files=files))

        return msg
