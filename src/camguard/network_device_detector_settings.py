from typing import Any, ClassVar, Dict
from camguard.settings import Settings


class NetworkDeviceDetectorSettings(Settings):
    """network device connector settings class
    """
    _KEY: ClassVar[str] = "network_device_detector"
    _DUMMY_MODE: ClassVar[str] = "dummy_mode"

    @property
    def dummy_mode(self) -> str:
        return self._dummy_mode

    @dummy_mode.setter
    def dummy_mode(self, value: str) -> None:
        self._dummy_mode = value

    def _parse_data(self, data: Dict[str, Any]):
        super()._parse_data(data)

        self.dummy_mode = super().get_setting_from_key(
            setting_key=f"{NetworkDeviceDetectorSettings._KEY}.{NetworkDeviceDetectorSettings._DUMMY_MODE}",
            settings=data, default=False)


class NMapDeviceDetectorSettings(NetworkDeviceDetectorSettings):
    """specialized mail notification settings for a common mail client implementation 
    """
    _KEY: ClassVar[str] = "nmap_device_detector"
    _IP_ADDR: ClassVar[str] = "ip_addr"
    _INTERVAL_SECONDS: ClassVar[str] = "interval_seconds"

    @property
    def ip_addr(self) -> str:
        return self._ip_addr

    @ip_addr.setter
    def ip_addr(self, value: str) -> None:
        self._ip_addr = value

    @property
    def interval_seconds(self) -> float:
        return self._interval_seconds

    @interval_seconds.setter
    def interval_seconds(self, value: float) -> None:
        self._interval_seconds = value

    def _parse_data(self, data: Dict[str, Any]):
        super()._parse_data(data)

        self.ip_addr = super().get_setting_from_key(
            setting_key=f"{super()._KEY}.{self._KEY}.{NMapDeviceDetectorSettings._IP_ADDR}",
            settings=data)

        self.interval_seconds = super().get_setting_from_key(
            setting_key=f"{super()._KEY}.{self._KEY}.{NMapDeviceDetectorSettings._INTERVAL_SECONDS}",
            settings=data)


class DummyNetworkDeviceDetectorSettings(NetworkDeviceDetectorSettings):
    """specialized mail notification settings for dummy implementation 
    """
    _KEY: ClassVar[str] = "dummy_network_device_detector"