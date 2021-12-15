from typing import Any, ClassVar, Dict, List
from camguard.settings import ImplementationType, Settings


class NetworkDeviceDetectorSettings(Settings):
    """network device connector settings class
    """
    _KEY: ClassVar[str] = 'network_device_detector'
    __IMPL_TYPE: ClassVar[str] = 'implementation'

    @property
    def impl_type(self) -> ImplementationType:
        return self._impl_type

    @impl_type.setter
    def impl_type(self, value: ImplementationType) -> None:
        self._impl_type = value

    def _parse_data(self, data: Dict[str, Any]):
        super()._parse_data(data)

        self.impl_type = ImplementationType.parse(super().get_setting_from_key(
            setting_key=f"{NetworkDeviceDetectorSettings._KEY}.{NetworkDeviceDetectorSettings.__IMPL_TYPE}",
            settings=data, 
            default=ImplementationType.DEFAULT.value))


class NMapDeviceDetectorSettings(NetworkDeviceDetectorSettings):
    """specialized mail notification settings for a common mail client implementation 
    """
    __KEY: ClassVar[str] = 'nmap_device_detector'
    __IP_ADDR: ClassVar[str] = 'ip_addr'
    __INTERVAL_SECONDS: ClassVar[str] = 'interval_seconds'

    @property
    def ip_addr(self) -> List[str]:
        return self.__ip_addr

    @ip_addr.setter
    def ip_addr(self, value: List[str]) -> None:
        self.__ip_addr = value

    @property
    def interval_seconds(self) -> float:
        return self._interval_seconds

    @interval_seconds.setter
    def interval_seconds(self, value: float) -> None:
        self._interval_seconds = value

    def _parse_data(self, data: Dict[str, Any]):
        super()._parse_data(data)

        self.ip_addr = super().get_setting_from_key(
            setting_key=f"{super()._KEY}.{self.__KEY}.{NMapDeviceDetectorSettings.__IP_ADDR}",
            settings=data)

        self.interval_seconds = super().get_setting_from_key(
            setting_key=f"{super()._KEY}.{self.__KEY}.{NMapDeviceDetectorSettings.__INTERVAL_SECONDS}",
            settings=data)


class DummyNetworkDeviceDetectorSettings(NetworkDeviceDetectorSettings):
    """specialized mail notification settings for dummy implementation 
    """
    _KEY: ClassVar[str] = 'dummy_network_device_detector'
