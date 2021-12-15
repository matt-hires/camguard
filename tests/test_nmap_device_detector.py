from subprocess import CompletedProcess
from time import sleep
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch
from camguard.dummy_network_device_detector import DummyNetworkDeviceDetector
from camguard.exceptions import CamguardError

from camguard.network_device_detector_settings import DummyNetworkDeviceDetectorSettings, NMapDeviceDetectorSettings
from camguard.nmap_device_detector import NMapDeviceDetector


class NmapDeviceDetectorTest(TestCase):

    @patch('camguard.nmap_device_detector.which', MagicMock(return_value=True))
    def setUp(self) -> None:
        self.__settings_mock = create_autospec(spec=NMapDeviceDetectorSettings, spec_set=True)
        type(self.__settings_mock).ip_addr = PropertyMock(return_value=['192.168.0.1', '192.168.0.2'])
        type(self.__settings_mock).interval_seconds = PropertyMock(return_value=1.0)

        self.__sut = NMapDeviceDetector(self.__settings_mock)

    @patch('camguard.nmap_device_detector.which', MagicMock(return_value=False))
    def test_should_raise_error_on_init(self):
        # arrange

        # act / assert
        with self.assertRaises(CamguardError):
            NMapDeviceDetector(self.__settings_mock)

    @patch('camguard.nmap_device_detector.run',
           MagicMock(return_value=CompletedProcess("nmap args", 0, "HoSt IS uP", None)))
    def test_should_call_handler(self):
        # arrange
        handler_mock = MagicMock()

        self.__sut.register_handler(handler_mock)

        # act
        self.__sut.start()
        sleep(self.__settings_mock.interval_seconds * 2)

        self.__sut.stop()
        handler_mock.assert_any_call([('192.168.0.1', True), ('192.168.0.2', True)])
        self.assertFalse(self.__sut.__getattribute__(f"_{NMapDeviceDetector.__name__}__thread"))

    def test_should_not_stop_when_never_started(self):
        # arrange

        # act
        self.__sut.stop()

        # assert
        self.assertFalse(self.__sut.__getattribute__(f"_{NMapDeviceDetector.__name__}__thread"))

    @patch('camguard.nmap_device_detector.run',
           MagicMock(return_value=CompletedProcess("nmap args", 0, "Nmap scan report: offline", None)))
    def test_should_stop_before_start_when_already_running(self):
        # arrange
        handler_mock = MagicMock()

        self.__sut.register_handler(handler_mock)

        # act
        self.__sut.start()
        self.__sut.start()

        self.__sut.stop()
        self.assertFalse(self.__sut.__getattribute__(f"_{NMapDeviceDetector.__name__}__thread"))

    @patch('camguard.nmap_device_detector.run',
           MagicMock(return_value=CompletedProcess("nmap args", 0, "Nmap scan report: offline", None)))
    def test_should_call_handler_when_offline(self):
        # arrange
        handler_mock = MagicMock()

        self.__sut.register_handler(handler_mock)

        # act
        self.__sut.start()
        sleep(self.__settings_mock.interval_seconds * 2)

        self.__sut.stop()
        handler_mock.assert_any_call([('192.168.0.1', False), ('192.168.0.2', False)])
        self.assertFalse(self.__sut.__getattribute__(f"_{NMapDeviceDetector.__name__}__thread"))

class DummyNetworkDeviceDetectorTest(TestCase):

    def setUp(self) -> None:
        self.__settings_mock = create_autospec(spec=DummyNetworkDeviceDetectorSettings, spec_set=True)

        self.__sut = DummyNetworkDeviceDetector(self.__settings_mock)

    @patch('camguard.dummy_network_device_detector.random', MagicMock(return_value=1))
    @patch('camguard.dummy_network_device_detector.uniform', MagicMock(return_value=1.0))
    def test_should_call_handler(self):
        # arrange
        handler_mock = MagicMock()

        self.__sut.register_handler(handler_mock)

        # act
        self.__sut.start()
        sleep(2)

        self.__sut.stop()
        handler_mock.assert_any_call([('Dummy', True)])
        self.assertFalse(self.__sut.__getattribute__(f"_{DummyNetworkDeviceDetector.__name__}__thread"))

    @patch('camguard.dummy_network_device_detector.random', MagicMock(return_value=0))
    @patch('camguard.dummy_network_device_detector.uniform', MagicMock(return_value=1))
    def test_should_call_handler_when_offline(self):
        # arrange
        handler_mock = MagicMock()

        self.__sut.register_handler(handler_mock)

        # act
        self.__sut.start()
        sleep(2)

        self.__sut.stop()
        handler_mock.assert_any_call([('Dummy', False)])
        self.assertFalse(self.__sut.__getattribute__(f"_{DummyNetworkDeviceDetector.__name__}__thread"))

    @patch('camguard.dummy_network_device_detector.random', MagicMock(return_value=0))
    @patch('camguard.dummy_network_device_detector.uniform', MagicMock(return_value=1))
    def test_should_stop_before_start_when_already_running(self):
        # arrange
        handler_mock = MagicMock()

        self.__sut.register_handler(handler_mock)

        # act
        self.__sut.start()
        self.__sut.start()

        self.__sut.stop()
        self.assertFalse(self.__sut.__getattribute__(f"_{DummyNetworkDeviceDetector.__name__}__thread"))

    def test_should_not_stop_when_never_started(self):
        # arrange

        # act
        self.__sut.stop()

        # assert
        self.assertFalse(self.__sut.__getattribute__(f"_{DummyNetworkDeviceDetector.__name__}__thread"))
