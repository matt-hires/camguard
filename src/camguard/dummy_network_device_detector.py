import logging
from random import uniform, random
from threading import Event, Thread
import threading
from typing import Callable, List, Optional, Tuple
from camguard.bridge_impl import NetworkDeviceDetectorImpl
from camguard.network_device_detector_settings import DummyNetworkDeviceDetectorSettings

LOGGER = logging.getLogger(__name__)


class DummyNetworkDeviceDetector(NetworkDeviceDetectorImpl):
    """dummy network device detector implementation with a random interval for simulation 
    """

    def __init__(self, settings: DummyNetworkDeviceDetectorSettings) -> None:
        """initialize dummy network device detector

        Args:
            settings (DummyNetworkDeviceDetectorSettings): dector settings from yaml 
        """
        super().__init__()
        self.__stop_event = Event()
        # skipcq: PTC-W0037
        self.__settings = settings
        self.__min_detection_seconds = 10.0
        self.__max_detection_seconds = 20.0
        self.__handler: Optional[Callable[[List[Tuple[str, bool]]], None]] = None
        self.__thread: Optional[Thread] = None

    def register_handler(self, handler: Callable[[List[Tuple[str, bool]]], None]) -> None:
        """registers a given handler, which will be called on device check

        Args:
            handler (Callable[[bool], None]): handler function to be called when device check runs 
        """
        LOGGER.debug("Registering nmap device detector callback")
        self.__handler = handler

    def start(self) -> None:
        """start the detection thread, stops an already running threads
        """
        LOGGER.info("Starting detector thread")
        if self.__thread:
            LOGGER.debug("Detector thread already running")
            self.stop()

        self.__thread = threading.Thread(target=self.__do_work)
        self.__thread.start()

    def stop(self) -> None:
        """stop nmap device detection thread, does nothing is thread has never been started
        """
        LOGGER.info("Stopping detector thread")
        # stop check thread
        if not self.__thread:
            LOGGER.debug("Detector thread has never been started")
            return
        self.__stop_event.set()
        self.__thread.join(4 * self.__max_detection_seconds)

        self.__stop_event.clear()
        self.__thread = None
        LOGGER.info("Shutdown successful")

    def __do_work(self):
        LOGGER.info("Starting device check thread")
        # check event in random interval
        while not self.__stop_event.wait(round(uniform(self.__min_detection_seconds,
                                                       self.__max_detection_seconds), 1)):
            # check for device in network
            LOGGER.debug("Simulating device detection")

            # randomize found device
            found_device: bool = bool(round(random()))
            found_devices: List[Tuple[str, bool]] = [('Dummy', found_device)]

            LOGGER.debug(f"Device detection state: {found_devices}")

            if self.__handler:
                # call handler and notice about detection status
                self.__handler(found_devices)

        LOGGER.info("Exiting device check thread")
