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
    def load_settings(cls, config_path: str, *, settings_file: str = "settings.yaml"):
        """load settings from yaml file path

        Args:
            filepath (str, optional): yaml file. Defaults to "settings.yaml".

        Raises:
            CamGuardError: if settings file cannot be openend 
            ConfigurationError: on yaml errors 

        Returns:
            Settings: an initialized Settings object 
        """
        settings_path: str = path.join(config_path, settings_file)
        LOGGER.info(f"Loading settings from: {settings_path}")

        instance = cls._create_instance()
        if not path.isfile(settings_path):
            LOGGER.debug(f"Ignore non existant settings: {settings_path}")
            return instance

        try:
            with open(settings_file, 'r') as stream:
                data = safe_load(stream)
        except OSError as ose:
            raise CamGuardError(f"Cannot open settings file {settings_file}: {ose}")
        except YAMLError as yamle:
            raise ConfigurationError(f"Error in settings file {settings_file}: {yamle}")
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
            cls.__init__(_instance)
        _instance._default()

        return _instance

    def _parse_data(self, data: Dict[str, str]):
        """parse data from yaml and store

        Args:
            data (Dict): yaml data dictionary
        """
        pass

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

        if not MotionHandlerSettings._KEY in data:
            raise ConfigurationError(f"Mandatory settings key not found: {MotionHandlerSettings._KEY}")

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
        self.record_path = "./record"
        self.record_interval_sec = 1.0
        self.record_count = 15
        self.record_file_format = "{counter:03d}_{timestamp:%y%m%d_%H%M%S}_capture.jpg"

    def _parse_data(self, data: Dict[Any, Any]):
        """parse settings data for raspi cam settings
        take care: in here self._KEY is used for key, this can be a different value than RaspiCamSettings._KEY,
        especially when using DummyCamSettings where this value will be overwritten
        """
        super()._parse_data(data)

        if not self._KEY in data[MotionHandlerSettings._KEY]:
            return # no mandatory values

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
        if not MotionDetectorSettings._KEY in data:
            raise ConfigurationError(f"Mandatory settings key not found: {MotionDetectorSettings._KEY}")

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

        if not self._KEY in data[MotionDetectorSettings._KEY]:
            raise ConfigurationError(f"Mandatory settings key not found: {MotionDetectorSettings._KEY}.{self._KEY}")

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
    _IMPL: ClassVar[str] = "implementation"
    _KEY: ClassVar[str] = "file_storage"

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

        if not FileStorageSettings._KEY in data:
            raise ConfigurationError(f"Mandatory settings key not found: {FileStorageSettings._KEY}")

        if FileStorageSettings._IMPL in data[FileStorageSettings._KEY]:
            self.impl_type = ImplementationType.parse(data[FileStorageSettings._KEY][FileStorageSettings._IMPL])


class GDriveStorageSettings(FileStorageSettings):
    """specialized gdrive storage setting
    """
    _UPLOAD_FOLDER_NAME: ClassVar[str] = "upload_folder_name"
    _KEY: ClassVar[str] = "gdrive_storage"

    @property
    def upload_folder_name(self) -> str:
        return self._upload_folder_name

    @upload_folder_name.setter
    def upload_folder_name(self, value: str) -> None:
        self._upload_folder_name = value

    def _default(self):
        super()._default()
        self.upload_folder_name = "Camguard"

    def _parse_data(self, data: Dict[Any, Any]):
        """parse settings data for gpio gdrive storage settings
        take care: in here self._KEY is used for key, this can be a different value than GDriveStorageSettings._KEY,
        especially when using GDriveDummyStorageSettings where this value will be overwritten
        """
        super()._parse_data(data)

        if not self._KEY in data[FileStorageSettings._KEY]:
            return # no mandator values

        if GDriveStorageSettings._UPLOAD_FOLDER_NAME in data[FileStorageSettings._KEY][self._KEY]:
            self.upload_folder_name = \
                data[FileStorageSettings._KEY][self._KEY][GDriveStorageSettings._UPLOAD_FOLDER_NAME]


class GDriveDummyStorageSettings(GDriveStorageSettings):
    """specialized gdrive dummy storage setting
    """
    _KEY: ClassVar[str] = "gdrive_dummy_storage"
