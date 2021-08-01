import logging
from enum import Enum
from os import path
from typing import Any, ClassVar, Dict

from yaml import safe_load
from yaml.error import YAMLError

from .exceptions import CamGuardError, ConfigurationError

LOGGER = logging.getLogger(__name__)


class ImplementationType(Enum):
    """implementation type setting for equipment selection
    """
    DUMMY = "dummy"
    RASPI = "raspi"

    @classmethod
    def parse(cls, value: str):
        if value == 'raspi':
            LOGGER.debug(f"{cls.__name__} - parsed implemenation type: raspi")
            return cls.RASPI
        elif value == 'dummy':
            LOGGER.debug(f"{cls.__name__} - parsed implemenation type: raspi")
            return cls.DUMMY
        else:
            raise ConfigurationError(f"Implementation type {value} not allowed")


class Settings:
    """camguard yaml settings base class
    """

    @classmethod
    def load_settings(cls, config_path: str, *, settings_file: str = "settings.yaml") -> Any:
        """load settings from yaml file path

        Args:
            filepath (str, optional): yaml file. Defaults to "settings.yaml".

        Raises:
            CamGuardError: if settings file cannot be openend 
            ConfigurationError: on yaml errors 

        Returns:
            Settings: an initialized Settings object 
        """
        resolved_path = path.expandvars(path.expanduser(config_path))
        settings_path = path.join(resolved_path, settings_file)
        LOGGER.info(f"{cls.__name__}: Loading settings from {settings_path}")

        instance = cls._create_instance()
        # altough every settings instance is pre-configured with default settings,
        # it's still necessary to have a settings file (for pin configuration, etc...)
        if not path.isfile(settings_path):
            raise ConfigurationError(f"{cls.__name__}: Settings path not found: {settings_path}")

        try:
            with open(settings_path, 'r') as stream:
                data = safe_load(stream)
        except OSError as ose:
            raise CamGuardError(f"{cls.__name__}: Cannot open settings file {settings_path}: {ose}")
        except YAMLError as yamle:
            raise ConfigurationError(f"{cls.__name__}: Error in settings file {settings_path}: {yamle}")
        else:
            instance._parse_data(data)

        return instance

    @classmethod
    def _create_instance(cls) -> Any:
        """create settings instance of given class and load default settings

        Returns:
            Any: the created class 
        """
        _instance = cls.__new__(cls)
        if isinstance(_instance, cls):
            # call initializer
            cls.__init__(_instance)  # type: ignore reportGeneralTypeIssues
        _instance._default()

        return _instance

    def _parse_data(self, data: Dict[str, str]):
        """parse data from yaml and store

        Args:
            data (Dict): yaml data dictionary
        """
        if not data:
            raise ConfigurationError("No configuration found")

    def _default(self):
        """generate default settings
        """
        pass


class MotionHandlerSettings(Settings):
    """Specialized motion handler settings class
    """
    _IMPL: ClassVar[str] = "implementation"
    _KEY: ClassVar[str] = "motion_handler"

    @property
    def impl_type(self) -> ImplementationType:
        return self._impl_type

    @impl_type.setter
    def impl_type(self, value: ImplementationType):
        self._impl_type = value

    def _default(self):
        super()._default()
        self.impl_type = ImplementationType.RASPI

    def _parse_data(self, data: Dict[Any, Any]):
        super()._parse_data(data)

        if not MotionHandlerSettings._KEY in data or not data[MotionHandlerSettings._KEY]:
            raise ConfigurationError(f"Mandatory settings key not found or empty: {MotionHandlerSettings._KEY}")

        if MotionHandlerSettings._IMPL in data[MotionHandlerSettings._KEY]:
            self.impl_type = ImplementationType.parse(data[MotionHandlerSettings._KEY][MotionHandlerSettings._IMPL])


class RaspiCamSettings(MotionHandlerSettings):
    """ specialized settings for raspi cam motion handler
    """
    _RECORD_PATH: ClassVar[str] = "record_path"
    _RECORD_INTERVAL_SEC: ClassVar[str] = "record_interval_seconds"
    _RECORD_COUNT: ClassVar[str] = "record_count"
    _RECORD_FILE_FORMAT: ClassVar[str] = "record_file_format"
    _KEY: ClassVar[str] = "raspi_cam"

    @property
    def record_path(self) -> str:
        return self._record_path

    @record_path.setter
    def record_path(self, value: str) -> None:
        self._record_path = value

    @property
    def record_interval_sec(self) -> float:
        return self._record_interval_sec

    @record_interval_sec.setter
    def record_interval_sec(self, value: float) -> None:
        self._record_interval_sec = value

    @property
    def record_count(self) -> int:
        return self._record_count

    @record_count.setter
    def record_count(self, value: int) -> None:
        self._record_count = value

    @property
    def record_file_format(self) -> str:
        return self._record_file_format

    @record_file_format.setter
    def record_file_format(self, value: str) -> None:
        self._record_file_format = value

    def _default(self):
        super()._default()
        self.record_path = "~/.camguard/records"
        self.record_interval_sec = 1.0
        self.record_count = 15
        self.record_file_format = "{counter:03d}_{timestamp:%y%m%d_%H%M%S}_capture.jpg"

    def _parse_data(self, data: Dict[Any, Any]):
        """parse settings data for raspi cam settings
        take care: in here self._KEY is used for key, this can be a different value than RaspiCamSettings._KEY,
        especially when using DummyCamSettings where this value will be overwritten
        """
        super()._parse_data(data)

        if not self._KEY in data[MotionHandlerSettings._KEY] or not data[MotionHandlerSettings._KEY][self._KEY]:
            return  # no mandatory values

        if RaspiCamSettings._RECORD_PATH in data[MotionHandlerSettings._KEY][self._KEY]:
            self.record_path = data[MotionHandlerSettings._KEY][self._KEY][RaspiCamSettings._RECORD_PATH]

        if RaspiCamSettings._RECORD_FILE_FORMAT in data[MotionHandlerSettings._KEY][self._KEY]:
            self.record_file_format = data[MotionHandlerSettings._KEY][self._KEY][RaspiCamSettings._RECORD_FILE_FORMAT]

        if RaspiCamSettings._RECORD_INTERVAL_SEC in data[MotionHandlerSettings._KEY][self._KEY]:
            self.record_interval_sec = data[MotionHandlerSettings._KEY][self._KEY][RaspiCamSettings._RECORD_INTERVAL_SEC]

        if RaspiCamSettings._RECORD_COUNT in data[MotionHandlerSettings._KEY][self._KEY]:
            self.record_count = data[MotionHandlerSettings._KEY][self._KEY][RaspiCamSettings._RECORD_COUNT]


class DummyCamSettings(RaspiCamSettings):
    """ specialized settings for dummy cam motion handler
    """
    _KEY: ClassVar[str] = "dummy_cam"


class MotionDetectorSettings(Settings):
    """Specialized motion detector settings class
    """
    _IMPL: ClassVar[str] = "implementation"
    _KEY: ClassVar[str] = "motion_detector"

    @property
    def impl_type(self) -> ImplementationType:
        return self._impl_type

    @impl_type.setter
    def impl_type(self, value: ImplementationType):
        self._impl_type = value

    def _default(self):
        super()._default()

        self.impl_type = ImplementationType.RASPI

    def _parse_data(self, data: Dict[Any, Any]):
        if not MotionDetectorSettings._KEY in data or not data[MotionDetectorSettings._KEY]:
            raise ConfigurationError(f"Mandatory settings key not found or empty: {MotionDetectorSettings._KEY}")

        if MotionDetectorSettings._IMPL in data[MotionDetectorSettings._KEY]:
            MotionDetectorSettings.impl_type = ImplementationType.parse(
                data[MotionDetectorSettings._KEY][MotionDetectorSettings._IMPL])


class RaspiGpioSensorSettings(MotionDetectorSettings):
    """Specialized motion detector settings for raspi gpio sensor
    """
    _GPIO_PIN_NUMBER: ClassVar[str] = "gpio_pin_number"
    _KEY: ClassVar[str] = "raspi_gpio_sensor"

    @property
    def gpio_pin_number(self) -> int:
        return self._gpio_pin_number

    @gpio_pin_number.setter
    def gpio_pin_number(self, value: int) -> None:
        self._gpio_pin_number = value

    def _parse_data(self, data: Dict[Any, Any]):
        """parse settings data for raspi gpio sensor settings
        take care: in here self._KEY is used for key, this can be a different value than RaspiGpioSensorSettings._KEY,
        especially when using DummyGpioSensorSettings where this value will be overwritten
        """
        super()._parse_data(data)

        if not self._KEY in data[MotionDetectorSettings._KEY] or not data[MotionDetectorSettings._KEY][self._KEY]:
            raise ConfigurationError("Mandatory settings key not found or empty: "
                                     f"{MotionDetectorSettings._KEY}.{self._KEY}")

        if not RaspiGpioSensorSettings._GPIO_PIN_NUMBER in data[MotionDetectorSettings._KEY][self._KEY]:
            raise ConfigurationError("Mandatory settings key not found: "
                                     f"{MotionDetectorSettings._KEY}.{self._KEY}."
                                     f"{RaspiGpioSensorSettings._GPIO_PIN_NUMBER}")

        self.gpio_pin_number = data[MotionDetectorSettings._KEY][self._KEY][RaspiGpioSensorSettings._GPIO_PIN_NUMBER]


class DummyGpioSensorSettings(RaspiGpioSensorSettings):
    """specialized motion detector settings for dummy gpio sensor
    """
    _KEY: ClassVar[str] = "dummy_gpio_sensor"


class FileStorageSettings(Settings):
    """specialized file storage settings class
    """
    _DUMMY_IMPL: ClassVar[str] = "dummy_implementation"
    _KEY: ClassVar[str] = "file_storage"

    @property
    def dummy_impl(self) -> bool:
        return self._dummy_impl

    @dummy_impl.setter
    def dummy_impl(self, value: bool):
        self._dummy_impl = value

    def _default(self):
        super()._default()
        self.dummy_impl = False

    def _parse_data(self, data: Dict[Any, Any]):
        super()._parse_data(data)

        if not FileStorageSettings._KEY in data or not data[FileStorageSettings._KEY]:
            raise ConfigurationError(f"Mandatory settings key not found or empty: {FileStorageSettings._KEY}")

        if FileStorageSettings._DUMMY_IMPL in data[FileStorageSettings._KEY]:
            self.dummy_impl = data[FileStorageSettings._KEY][FileStorageSettings._DUMMY_IMPL]


class GDriveStorageSettings(FileStorageSettings):
    """specialized gdrive storage setting
    """
    _UPLOAD_FOLDER_NAME: ClassVar[str] = "upload_folder_name"
    _KEY: ClassVar[str] = "gdrive_storage"
    _OAUTH_SETTINGS_PATH: ClassVar[str] = "oauth_settings_path"

    @property
    def upload_folder_name(self) -> str:
        return self._upload_folder_name

    @upload_folder_name.setter
    def upload_folder_name(self, value: str) -> None:
        self._upload_folder_name = value

    @property
    def oauth_settings_path(self) -> str:
        return self._oauth_settings_path

    @oauth_settings_path.setter
    def oauth_settings_path(self, value: str) -> None:
        self._oauth_settings_path = value

    def _default(self):
        super()._default()
        self.upload_folder_name = "Camguard"
        self.oauth_settings_path = "google-oauth-settings.yaml"

    def _parse_data(self, data: Dict[Any, Any]):
        """parse settings data for gpio gdrive storage settings
        take care: in here self._KEY is used for key, this can be a different value than GDriveStorageSettings._KEY,
        especially when using DummyGDriveStorageSettings where this value will be overwritten
        """
        super()._parse_data(data)

        if not self._KEY in data[FileStorageSettings._KEY] or not data[FileStorageSettings._KEY][self._KEY]:
            return  # no mandator values

        if GDriveStorageSettings._UPLOAD_FOLDER_NAME in data[FileStorageSettings._KEY][self._KEY]:
            self.upload_folder_name = \
                data[FileStorageSettings._KEY][self._KEY][GDriveStorageSettings._UPLOAD_FOLDER_NAME]

        if GDriveStorageSettings._OAUTH_SETTINGS_PATH in data[FileStorageSettings._KEY][self._KEY]:
            self.oauth_settings_path = \
                data[FileStorageSettings._KEY][self._KEY][GDriveStorageSettings._OAUTH_SETTINGS_PATH]


class DummyGDriveStorageSettings(GDriveStorageSettings):
    """specialized gdrive dummy storage setting
    """
    _KEY: ClassVar[str] = "dummy_gdrive_storage"


class MailClientSettings(Settings):
    """specialized mail notificationsettings class
    """
    _DUMMY_IMPL: ClassVar[str] = "dummy_implementation"
    _KEY: ClassVar[str] = "mail_client"
    _USER: ClassVar[str] = "username"
    _PASSWORD: ClassVar[str] = "password"
    _RECEIVER_MAIL: ClassVar[str] = "receiver_mail"
    _SENDER_MAIL: ClassVar[str] = "sender_mail"
    _HOSTNAME: ClassVar[str] = "hostname"

    @property
    def dummy_impl(self) -> bool:
        return self._dummy_impl

    @dummy_impl.setter
    def dummy_impl(self, value: bool):
        self._dummy_impl = value

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

    def _default(self):
        super()._default()
        self.dummy_impl = False

    def _parse_data(self, data: Dict[Any, Any]):
        super()._parse_data(data)

        if not MailClientSettings._KEY in data or not data[MailClientSettings._KEY]:
            raise ConfigurationError(f"Mandatory settings key not found or empty: {MailClientSettings._KEY}")

        if MailClientSettings._DUMMY_IMPL in data[MailClientSettings._KEY]:
            self.dummy_impl = data[MailClientSettings._KEY][MailClientSettings._DUMMY_IMPL]

        if not MailClientSettings._USER in data[MailClientSettings._KEY]:
            raise ConfigurationError("Mandatory settings key not found: "
                                     f"{MailClientSettings._KEY}.{MailClientSettings._USER}")
        self.user = data[MailClientSettings._KEY][MailClientSettings._USER]

        if not MailClientSettings._PASSWORD in data[MailClientSettings._KEY]:
            raise ConfigurationError("Mandatory settings key not found: "
                                     f"{MailClientSettings._KEY}.{MailClientSettings._PASSWORD}")
        self.password = data[MailClientSettings._KEY][MailClientSettings._PASSWORD]

        if not MailClientSettings._RECEIVER_MAIL in data[MailClientSettings._KEY]:
            raise ConfigurationError("Mandatory settings key not found: "
                                     f"{MailClientSettings._KEY}.{MailClientSettings._RECEIVER_MAIL}")
        self.receiver_mail = data[MailClientSettings._KEY][MailClientSettings._RECEIVER_MAIL]

        if not MailClientSettings._SENDER_MAIL in data[MailClientSettings._KEY]:
            raise ConfigurationError("Mandatory settings key not found: "
                                     f"{MailClientSettings._KEY}.{MailClientSettings._SENDER_MAIL}")
        self.sender_mail = data[MailClientSettings._KEY][MailClientSettings._SENDER_MAIL]

        if not MailClientSettings._HOSTNAME in data[MailClientSettings._KEY]:
            raise ConfigurationError("Mandatory settings key not found: "
                                     f"{MailClientSettings._KEY}.{MailClientSettings._HOSTNAME}")
        self.hostname = data[MailClientSettings._KEY][MailClientSettings._HOSTNAME]


class GenericMailClientSettings(MailClientSettings):
    """specialized mail notification settings for a common mail client implementation 
    """
    _KEY: ClassVar[str] = "generic_mail_client"


class DummyMailClientSettings(MailClientSettings):
    """specialized mail notification settings for dummy implementation 
    """
    _KEY: ClassVar[str] = "dummy_mail_client"
