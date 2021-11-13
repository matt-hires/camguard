from typing import Any, ClassVar, Dict
from camguard.settings import ImplementationType, Settings


class MotionHandlerSettings(Settings):
    """Specialized motion handler settings class
    """
    _IMPL: ClassVar[str] = 'implementation'
    _KEY: ClassVar[str] = 'motion_handler'

    @property
    def impl_type(self) -> ImplementationType:
        return self._impl_type

    @impl_type.setter
    def impl_type(self, value: ImplementationType):
        self._impl_type = value

    def _parse_data(self, data: Dict[Any, Any]):
        super()._parse_data(data)

        self.impl_type = ImplementationType.parse(super().get_setting_from_key(
            setting_key=f"{MotionHandlerSettings._KEY}.{MotionHandlerSettings._IMPL}",
            settings=data,
            default=ImplementationType.RASPI))


class RaspiCamSettings(MotionHandlerSettings):
    """ specialized settings for raspi cam motion handler
    """
    _RECORD_PATH: ClassVar[str] = 'record_path'
    _RECORD_INTERVAL_SEC: ClassVar[str] = 'record_interval_seconds'
    _RECORD_COUNT: ClassVar[str] = 'record_count'
    _RECORD_FILE_FORMAT: ClassVar[str] = 'record_file_format'
    _KEY: ClassVar[str] = 'raspi_cam'

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

    def _parse_data(self, data: Dict[Any, Any]):
        """parse settings data for raspi cam settings
        take care: in here self._KEY is used for key, this can be a different value than RaspiCamSettings._KEY,
        especially when using DummyCamSettings where this value will be overwritten
        """
        super()._parse_data(data)

        self.record_path = super().get_setting_from_key(
            setting_key=f"{MotionHandlerSettings._KEY}.{self._KEY}.{RaspiCamSettings._RECORD_PATH}",
            settings=data,
            default="$HOME/.camguard/records"
        )

        self.record_file_format = super().get_setting_from_key(
            setting_key=f"{MotionHandlerSettings._KEY}.{self._KEY}.{RaspiCamSettings._RECORD_FILE_FORMAT}",
            settings=data,
            default="{counter:03d}_{timestamp:%y%m%d_%H%M%S%f}_capture.jpg"
        )

        self.record_interval_sec = super().get_setting_from_key(
            setting_key=f"{MotionHandlerSettings._KEY}.{self._KEY}.{RaspiCamSettings._RECORD_INTERVAL_SEC}",
            settings=data,
            default=1.0
        )

        self._record_count = super().get_setting_from_key(
            setting_key=f"{MotionHandlerSettings._KEY}.{self._KEY}.{RaspiCamSettings._RECORD_COUNT}",
            settings=data,
            default=15
        )


class DummyCamSettings(RaspiCamSettings):
    """ specialized settings for dummy cam motion handler
    """
    _KEY: ClassVar[str] = 'dummy_cam' # override key for DummyCamSettings
