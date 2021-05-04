from os import path
from typing import Dict
from yaml import safe_load
from yaml.error import YAMLError

from camguard.exceptions import CamGuardError, ConfigurationError
from enum import Enum


class ImplementationType(Enum):
    """implementation type setting for equipment selection
    """
    DUMMY = "dummy"
    RASPI = "raspi"

    @classmethod
    def parse(cls, value):
        if value == 'raspi':
            return cls.RASPI
        if value == 'dummy':
            return cls.DUMMY
        else:
            raise ConfigurationError(f"Implementation type {value} not allowed")


class Settings:
    """camguard yaml settings base class
    """
    _instance = None

    @classmethod
    def load_settings(cls, filepath="settings.yaml"):
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

    def _parse_data(self, data: Dict):
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

    def _parse_data(self, data: Dict):
        super()._parse_data()

        if self._IMPL in data[self._KEY]:
            self.impl_type = ImplementationType.parse(data[self._KEY][self._IMPL])


class MotionDetectorSettings(Settings):
    """Specialized motion detector settings class
    """
    _KEY = "motion_detector"
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

    def _parse_data(self, data: Dict):
        super()._parse_data()

        if self._IMPL in data[self._KEY]:
            self.impl_type = ImplementationType.parse(data[self._KEY][self._IMPL])
