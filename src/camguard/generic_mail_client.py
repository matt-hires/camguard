
import logging
from os import path
from email.message import EmailMessage
from smtplib import SMTP as Client
from smtplib import SMTPConnectError
from typing import ClassVar, List

from camguard.bridge_impl import MailClientImpl
from camguard.mail_client_settings import GenericMailClientSettings

LOGGER = logging.getLogger(__name__)


class GenericMailClient(MailClientImpl):
    """generic smtp mail client implementation, supports sending notification mails to a configured receiver mail
    """
    __PORT: ClassVar[int] = 587  # for starttls
    __MAIL_MSG: ClassVar[str] = "Camguard motion triggered, files where recorded and uploaded: {files}"
    __MAIL_SUBJECT: ClassVar[str] = "Camguard motion triggered"

    def __init__(self, settings: GenericMailClientSettings) -> None:
        """initialize generic mail client with settings from yaml
        """
        self.__settings = settings

    def send_mail(self, files: List[str]) -> None:
        """send mail to configured receiver to notify about recorded files list

        Args:
            files (List[str]): the list of already recorded files to inform about
        """
        LOGGER.info(f"Sending mail with: {files}")
        sender = self.__settings.sender_mail
        receiver = self.__settings.receiver_mail

        try:
            with Client(host=self.__settings.hostname, port=GenericMailClient.__PORT) as client:
                client.starttls()
                client.login(self.__settings.user, self.__settings.password)
                client.send_message(GenericMailClient.__create_msg(sender, receiver, files))
        except (SMTPConnectError, OSError) as client_err:
            LOGGER.error("Error while connecting to mail server: "
                         f"{self.__settings.hostname}:{GenericMailClient.__PORT}",
                         exc_info=client_err)

    @staticmethod
    def __create_msg(sender: str, receiver: str, files: List[str]) -> EmailMessage:
        msg: EmailMessage = EmailMessage()
        msg.add_header('Subject', GenericMailClient.__MAIL_SUBJECT)
        msg.add_header('From', sender)
        msg.add_header('To', receiver)
        msg.set_content(GenericMailClient.__MAIL_MSG.format(files=[path.basename(file) for file in files]))

        return msg
