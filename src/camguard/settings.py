import logging
from os import path
from typing import Any, Dict, List

from yaml import safe_load
from yaml.error import YAMLError

from camguard.exceptions import CamguardError, ConfigurationError
from camguard.extended_enum import ExtendedEnum

LOGGER = logging.getLogger(__name__)


class ImplementationType(ExtendedEnum):
    """implementation type setting for equipment selection
    """
    DUMMY = "dummy"
    RASPI = "raspi"
    DEFAULT = "default"

    @classmethod
    def parse(cls, value: str):
        enum_vals = cls.list_values()
        logger = logging.getLogger(cls.__name__) # log with specific cls name

        if value not in enum_vals:
            raise ConfigurationError(f"Implementation type {value} not allowed. "
                                     f"Allowed values are: {enum_vals}")

        logger.debug(f"Parsing implementation type: {value}")

        if value == cls.RASPI.value:
            return cls.RASPI
        if value == cls.DUMMY.value:
            return cls.DUMMY

        return ImplementationType.DEFAULT

class Settings:
    """camguard yaml settings base class
    """

    @classmethod
    def load_settings(cls, config_path: str, *, settings_file: str = "settings.yaml") -> Any:
        """load settings from yaml file path

        Args:
            filepath (str, optional): yaml file. Defaults to "settings.yaml".

        Raises:
            CamguardError: if settings file cannot be openend 
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
            raise CamguardError(f"{cls.__name__}: Cannot open settings file {settings_path}: {ose}")
        except YAMLError as yamle:
            raise ConfigurationError(f"{cls.__name__}: Error in settings file {settings_path}: {yamle}")
        else:
            instance._parse_data(data)

        return instance

    @classmethod
    def get_setting_from_key(cls, setting_key: str, settings: Dict[str, Any], default: Any = None) -> Any:
        """getting a specific from a settings key

        Args:
            setting_key (str): key to get settings from dict, subkeys can be referenced by '.' i.e. 'key1.subkey1'
            settings (Dict[str, Any]): the settings dictionary to retrieve the setting from
            default (Any, optional): specifies setting as optional and assigns a default value. Defaults to None.

        Raises:
            ConfigurationError: when setting is not found or empty and non-optional

        Returns:
            Any: the given setting value in the dictionary
        """

        splitted_key: List[str] = setting_key.split('.')

        value: Any = settings
        for key in splitted_key:
            if key in value and value[key]:
                value = value[key]
            else:
                value = None
                break

        if value is None and default is None:
            raise ConfigurationError(f"Mandatory settings key not found: {setting_key}")

        if value is None and default is not None:
            return default

        return value

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

        return _instance

    # skipcq: PYL-R0201
    def _parse_data(self, data: Dict[str, Any]):
        """parse data from yaml and store

        Args:
            data (Dict): yaml data dictionary
        """
        if not data:
            raise ConfigurationError("No configuration found")
