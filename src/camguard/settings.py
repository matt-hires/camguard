from os import path
from typing import Any, Dict
from yaml import safe_load
from yaml.error import YAMLError

from .exceptions import CamGuardError, ConfigurationError
from enum import Enum
import logging

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
    _instance = None

    @classmethod
    def load_settings(cls, filepath: str = "settings.yaml"):
        """load settings from yaml file path

        Args:
            filepath (str, optional): yaml file. Defaults to "settings.yaml".

        Raises:
            CamGuardError: if settings file cannot be openend 
            ConfigurationError: on yaml errors 

        Returns:
            Settings: an initialized Settings object 
        """
        instance = cls._create_instance()

        if not path.isfile(filepath):
            LOGGER.debug(f"Ignore non existant settings: {filepath}")
            return instance

        try:
            with open(filepath, 'r') as stream:
                data = safe_load(stream)
        except OSError as ose:
            raise CamGuardError(f"Cannot open settings file {filepath}: {ose}")
        except YAMLError as yamle:
            raise ConfigurationError(f"Error in settings file {filepath}: {yamle}")
        else:
            instance._parse_data(data)

        return instance

    @classmethod
    def _create_instance(cls):
        """create the one and only settings object
        this is class method so it is also possible to use this for subclasses

        Returns:
           Settings: the settings object or it's derivation class
        """
        if not cls._instance:
            cls._instance = cls.__new__(cls)
            # init default settings
            cls._instance._default()

        return cls._instance

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
    _KEY = "motion_handler"
    _IMPL = "implementation"

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

        if self._IMPL in data[self._KEY]:
            self.impl_type = ImplementationType.parse(data[self._KEY][self._IMPL])


class MotionDetectorSettings(Settings):
    """Specialized motion detector settings class
    """
    _KEY: str = "motion_detector"
    _IMPL: str = "implementation"

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

        if self._IMPL in data[self._KEY]:
            self.impl_type = ImplementationType.parse(data[self._KEY][self._IMPL])


class FileStorageSettings(Settings):
    """specialized file storage settings class
    """
    _KEY: str = "file_storage"
    _IMPL: str = "implementation"

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

        if self._IMPL in data[self._KEY]:
            self.impl_type = ImplementationType.parse(data[self._KEY][self._IMPL])
