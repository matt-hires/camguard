from typing import Any, ClassVar, Dict
from camguard.settings import ImplementationType, Settings


class MailClientSettings(Settings):
    """specialized mail notificationsettings class
    """
    _IMPL_TYPE: ClassVar[str] = "implementation"
    _KEY: ClassVar[str] = "mail_client"
    _USER: ClassVar[str] = "username"
    _PASSWORD: ClassVar[str] = "password"
    _RECEIVER_MAIL: ClassVar[str] = "receiver_mail"
    _SENDER_MAIL: ClassVar[str] = "sender_mail"
    _HOSTNAME: ClassVar[str] = "hostname"

    @property
    def impl_type(self) -> ImplementationType:
        return self._impl_type

    @impl_type.setter
    def impl_type(self, value: ImplementationType):
        self._impl_type = value

    @property
    def user(self) -> str:
        return self._user

    @user.setter
    def user(self, username: str) -> None:
        self._user = username

    @property
    def password(self) -> str:
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        self._password = password

    @property
    def receiver_mail(self) -> str:
        return self._receiver_mail

    @receiver_mail.setter
    def receiver_mail(self, receiver: str) -> None:
        self._receiver_mail = receiver

    @property
    def sender_mail(self) -> str:
        return self._sender_mail

    @sender_mail.setter
    def sender_mail(self, sender: str) -> None:
        self._sender_mail = sender

    @property
    def hostname(self) -> str:
        return self._hostname

    @hostname.setter
    def hostname(self, hostname: str) -> None:
        self._hostname = hostname

    def _parse_data(self, data: Dict[str, Any]):
        super()._parse_data(data)

        self.impl_type = ImplementationType.parse(super().get_setting_from_key(
            setting_key=f"{MailClientSettings._KEY}.{MailClientSettings._IMPL_TYPE}",
            settings=data,
            default=ImplementationType.DEFAULT.value
        ))

        self.user = super().get_setting_from_key(
            setting_key=f"{MailClientSettings._KEY}.{MailClientSettings._USER}",
            settings=data
        )

        self.password = super().get_setting_from_key(
            setting_key=f"{MailClientSettings._KEY}.{MailClientSettings._PASSWORD}",
            settings=data
        )

        self.receiver_mail = super().get_setting_from_key(
            setting_key=f"{MailClientSettings._KEY}.{MailClientSettings._RECEIVER_MAIL}",
            settings=data
        )

        self.sender_mail = super().get_setting_from_key(
            setting_key=f"{MailClientSettings._KEY}.{MailClientSettings._SENDER_MAIL}",
            settings=data
        )

        self.hostname = super().get_setting_from_key(
            setting_key=f"{MailClientSettings._KEY}.{MailClientSettings._HOSTNAME}",
            settings=data
        )


class GenericMailClientSettings(MailClientSettings):
    """specialized mail notification settings for a common mail client implementation 
    """
    _KEY: ClassVar[str] = "generic_mail_client"


class DummyMailClientSettings(MailClientSettings):
    """specialized mail notification settings for dummy implementation 
    """
    _KEY: ClassVar[str] = "dummy_mail_client"
