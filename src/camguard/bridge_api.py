from functools import wraps
import logging
from threading import Lock
from typing import Any, Callable, Generator, List, Tuple

from camguard.bridge_impl import FileStorageImpl, MailClientImpl, MotionDetectorImpl, MotionHandlerImpl, NetworkDeviceDetectorImpl
from camguard.file_storage_settings import DummyGDriveStorageSettings, FileStorageSettings, GDriveStorageSettings
from camguard.mail_client_settings import DummyMailClientSettings, GenericMailClientSettings, MailClientSettings
from camguard.motion_detector_settings import DummyGpioSensorSettings, MotionDetectorSettings, RaspiGpioSensorSettings
from camguard.motion_handler_settings import DummyCamSettings, MotionHandlerSettings, RaspiCamSettings
from camguard.network_device_detector_settings import DummyNetworkDeviceDetectorSettings, NMapDeviceDetectorSettings, NetworkDeviceDetectorSettings
from camguard.settings import ImplementationType

LOGGER = logging.getLogger(__name__)


def pipelinestep(func: Callable[..., Any]):
    """interceptor function for priming coroutines 
    before first usage. In this context it is used to declare a motion handler
    pipeline step. Simply put @pipelinestep above function 
    to use it
    """
    @wraps(func)  # make it look like the wrapped 'func'
    def _wrapper(*args: Any, **kwargs: Any) -> Generator[Any, Any, Any]:
        gen = func(*args, **kwargs)
        try:
            next(gen)
        except StopIteration:
            LOGGER.error(f"Generator function is exhausted: {gen.__module__}.{gen.__name__}")
            pass
        return gen
    return _wrapper


class MotionHandler:
    """ motion handler api class which supports handler pipeline usage
    """

    def __init__(self, config_path: str) -> None:
        """default initialization

        Args:
            record_root_path (str): root path where to record files
            config_path (str): settings configuration path
        """
        self._config_path = config_path
        self._settings = MotionHandlerSettings.load_settings(config_path)
        self._get_impl()  # create impl objects

    @pipelinestep
    def on_motion(self, pipeline: List[Generator[None, Any, None]]) -> Generator[None, 'MotionDetector', None]:
        """ motion handler pipeline step: on_motion
        handle current motion event in handler and sends return value to sink pipeline

        Yields:
            Generator[None, object, None]: motiondetector object which detected motion
        """
        while True:
            detector: MotionDetector = (yield)
            LOGGER.info(f"Detected motion on detector with id: {detector.id}")
            LOGGER.debug("Forwarding event to pipeline")
            ret_val = self._get_impl().handle_motion()
            for step in pipeline:
                step.send(ret_val)

    def stop(self) -> None:
        """stop motion handler
        """
        self._get_impl().shutdown()

    @property
    def id(self) -> int:
        """get handler identifier

        Returns:
            int: identifier as int
        """
        return self._get_impl().id

    def _get_impl(self) -> MotionHandlerImpl:
        """initializes implementation classes, if not already done

        Returns:
            MotionHandlerImpl: the configured implementation class
        """
        if not hasattr(self, '_impl') or not self._impl:
            if self._settings.impl_type == ImplementationType.DUMMY:
                from .dummy_cam import DummyCam
                self._impl = DummyCam(DummyCamSettings.load_settings(self._config_path))
            else:
                # defaults to raspi cam implementation
                from .raspi_cam import RaspiCam
                self._impl = RaspiCam(RaspiCamSettings.load_settings(self._config_path))

        return self._impl


class MotionDetector:
    """ motion detector api class, which supports handler pipeline usage
    """

    _lock: Lock = Lock()

    def __init__(self, config_path: str) -> None:
        """default initialization

        Args:
            config_path (str): settings configuration path
        """
        self._pipeline: List[Generator[None, 'MotionDetector', None]] = []
        self._config_path = config_path
        self._settings: MotionDetectorSettings = MotionDetectorSettings.load_settings(config_path)
        self._get_impl()  # create impl objects

    def register_handlers(self, pipeline: List[Generator[None, 'MotionDetector', None]]) -> None:
        """register handler pipe

        Args:
            pipeline (List[Generator[None, object, None]]): array of gen based 
            coroutines to build a handler pipe which will be called when motion occurs 
        """
        self._pipeline = pipeline
        self._get_impl().register_handler(self.__on_motion)

    def stop(self) -> None:
        """shutdown sensor, stops motion detection 
        """
        self._get_impl().shutdown()

    @property
    def id(self) -> int:
        """motion detector identifier

        Returns:
            int: identifier as int
        """
        return self._get_impl().id

    @property
    def disabled(self) -> bool:
        """get disabled flag - thread safe

        Returns:
            bool: the disabled state as boolean
        """
        # synchronize for enabling cross-thread calls for this function
        with MotionDetector._lock:
            return self._get_impl().disabled

    def on_disable(self, ips: List[Tuple[str, bool]]) -> None:
        """handler function for disabling handler from network device detector

        Args:
            ips (List[Tuple[str, bool]]): detected network device ips
        """
        # synchronize for enabling cross-thread calls for this function
        with MotionDetector._lock:
            self._get_impl().on_disable(ips)

    def __on_motion(self) -> None:
        """forward motion event to handler pipeline
        """
        LOGGER.debug("Forwarding event to motion handler pipeline")
        for step in self._pipeline:
            step.send(self)

    def _get_impl(self) -> MotionDetectorImpl:
        """initializes implementation classes, if not already done

        Returns:
            MotionDetectorImpl: the configured implementation class
        """
        if not hasattr(self, '_impl') or not self._impl:
            if self._settings.impl_type == ImplementationType.DUMMY:
                from .dummy_gpio_sensor import DummyGpioSensor
                self._impl = DummyGpioSensor(DummyGpioSensorSettings.load_settings(self._config_path))
            else:
                # defaults to raspi cam implementation
                from .raspi_gpio_sensor import RaspiGpioSensor
                self._impl = RaspiGpioSensor(RaspiGpioSensorSettings.load_settings(self._config_path))

        return self._impl


class FileStorage:
    """ file storage api class, which supports handler pipeline usage
    """

    def __init__(self, config_path: str) -> None:
        """default initialization

        Args:
            config_path (str): settings configuration path
        """
        self._config_path = config_path
        self._settings: FileStorageSettings = FileStorageSettings.load_settings(self._config_path)
        self._get_impl()  # create impl objects

    def authenticate(self) -> None:
        """authenticate to storage
        """
        self._get_impl().authenticate()

    def start(self) -> None:
        """start storage worker
        """
        self._get_impl().start()

    def stop(self) -> None:
        """stop storage worker
        """
        self._get_impl().stop()

    @pipelinestep
    def enqueue_files(self) -> Generator[None, List[str], None]:
        """motion handler pipeline step: enqueue files 

        Yields:
            Generator[None, List[str], None]: file path array which will be enqueued
        """
        while True:
            files: List[str] = (yield)
            LOGGER.debug("Retrieving files from pipeline")
            self._get_impl().enqueue_files(files)

    def _get_impl(self) -> FileStorageImpl:
        """initializes implementation classes, if not already done

        Returns:
            FileStorageImpl: the configured implementation class
        """
        if not hasattr(self, '_impl') or not self._impl:
            if self._settings.impl_type == ImplementationType.DUMMY:
                from .dummy_gdrive_storage import DummyGDriveStorage
                self._impl = DummyGDriveStorage(DummyGDriveStorageSettings.load_settings(self._config_path))
            else:
                from .gdrive_storage import GDriveStorage
                self._impl = GDriveStorage(GDriveStorageSettings.load_settings(self._config_path))

        return self._impl


class MailClient:
    """mail notification api class, which supports handler pipeline usage
    """

    def __init__(self, config_path: str) -> None:
        """default initialization

        Args:
            config_path (str): settings configuration path
        """
        self._config_path = config_path
        self._settings: MailClientSettings = MailClientSettings.load_settings(self._config_path)
        self._get_impl()  # create impl objects

    @pipelinestep
    def send_mail(self) -> Generator[None, List[str], None]:
        """motion handler pipeline step: send notification mail

        Yields:
            Generator[None, str, None]: gdrive link to folder which will be included in mail
        """
        while True:
            files: List[str] = (yield)
            LOGGER.debug("Retrieving files from pipeline")
            self._get_impl().send_mail(files)

    def _get_impl(self) -> MailClientImpl:
        """initializes implementation classes, if not already done

        Returns:
            MailClientImpl: the configured implementation class
        """
        if not hasattr(self, '_impl') or not self._impl:
            if self._settings.impl_type == ImplementationType.DUMMY:
                from .dummy_mail_client import DummyMailClient
                self._impl = DummyMailClient(DummyMailClientSettings.load_settings(self._config_path))
            else:
                from .generic_mail_client import GenericMailClient
                self._impl = GenericMailClient(GenericMailClientSettings.load_settings(self._config_path))

        return self._impl


class NetworkDeviceDetector:
    """network device detector api class
    """

    def __init__(self, config_path: str) -> None:
        """default initialization

        Args:
            config_path (str): settings configuration path
        """
        self._config_path = config_path
        self._settings: NetworkDeviceDetectorSettings = NetworkDeviceDetectorSettings.load_settings(self._config_path)
        self._get_impl()  # create impl objects

    def register_handler(self, handler: Callable[[List[Tuple[str, bool]]], None]):
        """register callback function, which will be triggered everytime 
        the check algorithm returns a result.

        Args:
            handler (Callable[[List[Tuple[str, bool]]], None]): function which will be called, 
            passing a parameter which contains the ips with their detection state 
        """
        self._get_impl().register_handler(handler)

    def start(self) -> None:
        """start the detector thread
        """
        self._get_impl().start()

    def stop(self) -> None:
        """stop the detector thread
        """
        self._get_impl().stop()

    def _get_impl(self) -> NetworkDeviceDetectorImpl:
        """initializes implementation classes, if not already done

        Returns:
            NetworkDeviceDetectorImpl: the configured implementation class
        """
        if not hasattr(self, '_impl') or not self._impl:
            if self._settings.impl_type == ImplementationType.DUMMY:
                from .dummy_network_device_detector import DummyNetworkDeviceDetector
                self._impl = DummyNetworkDeviceDetector(
                    DummyNetworkDeviceDetectorSettings.load_settings(self._config_path))
            else:
                from .nmap_device_detector import NMapDeviceDetector
                self._impl = NMapDeviceDetector(NMapDeviceDetectorSettings.load_settings(self._config_path))

        return self._impl
