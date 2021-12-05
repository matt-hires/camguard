import logging
from typing import Any, ClassVar, Dict, List

from camguard.exceptions import CamguardError, ConfigurationError
from camguard.extended_enum import ExtendedEnum
from camguard.settings import Settings

LOGGER = logging.getLogger(__name__)


class ComponentsType(ExtendedEnum):
    """Components types for equipment selection
    """
    MOTION_HANDLER = ('motion_handler', True)
    MOTION_DETECTOR = ('motion_detector', True)
    FILE_STORAGE = ('file_storage', False)
    MAIL_CLIENT = ('mail_client', False)
    NETWORK_DEVICE_DETECTOR = ('network_device_detector', False)

    def __init__(self, component_name: str, mandatory: bool) -> None:
        super().__init__()
        self.__component_name = component_name
        self.__mandatory = mandatory

    @property
    def component_name(self) -> str:
        return self.__component_name

    @property
    def mandatory(self) -> bool:
        return self.__mandatory

    @classmethod
    def check_mandatory(cls, components: List['ComponentsType']) -> List['str']:
        """checks mandatory components from a given list and returns missing mandatories, if any

        Returns:
            List[str]: list of missing, mandatory component names
        """
        missing_components: List[str] = []

        for component in cls.list(lambda e: e):
            if component.mandatory and component not in components:
                missing_components.append(component.component_name)

        return missing_components

    @classmethod
    def parse(cls, value: str):
        enum_vals = cls.list(lambda e: e.component_name)
        logger = logging.getLogger(cls.__name__)  # log with specific cls name

        if value not in enum_vals:
            raise ConfigurationError(f"Component type {value} not allowed. "
                                     f"Allowed values are: {enum_vals}")

        logger.debug(f"Parsing component type: {value}")

        if value == cls.MOTION_HANDLER.component_name:
            return cls.MOTION_HANDLER
        if value == cls.MOTION_DETECTOR.component_name:
            return cls.MOTION_DETECTOR
        if value == cls.FILE_STORAGE.component_name:
            return cls.FILE_STORAGE
        if value == cls.MAIL_CLIENT.component_name:
            return cls.MAIL_CLIENT
        if value == cls.NETWORK_DEVICE_DETECTOR.component_name:
            return cls.NETWORK_DEVICE_DETECTOR

        raise CamguardError(f"Component type {value} not implemented yet")


class CamguardSettings(Settings):
    """General settings for camguard application 
    """
    __COMPONENTS: ClassVar[str] = 'components'

    @property
    def components(self) -> List[ComponentsType]:
        return self.__components

    @components.setter
    def components(self, value: List[ComponentsType]):
        self.__components = value

    def _parse_data(self, data: Dict[str, Any]):
        super()._parse_data(data)

        self.components = [ComponentsType.parse(component) for component in super().get_setting_from_key(
            setting_key=self.__COMPONENTS, settings=data)
        ]

        missing_mandatories = ComponentsType.check_mandatory(self.__components)
        if missing_mandatories:
            raise ConfigurationError(f"Mandatory components missing: {missing_mandatories}")
