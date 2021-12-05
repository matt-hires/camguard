import logging
import threading
from shutil import which
from subprocess import run
from threading import Event, Thread
from typing import Callable, ClassVar, List, Optional

from camguard.bridge_impl import NetworkDeviceDetectorImpl
from camguard.exceptions import CamguardError
from camguard.network_device_detector_settings import \
    NMapDeviceDetectorSettings

LOGGER = logging.getLogger(__name__)


class NMapDeviceDetector(NetworkDeviceDetectorImpl):
    """nmap device detector implementation, which detects a configured device on a configured network and calls a
    handler passing the detection state 

    Raises:
        CamguardError: if nmap binary cannot be found on system
    """
    __NMAP_BIN: ClassVar[str] = 'nmap'
    __SCAN_TYPE: ClassVar[str] = '-sn'
    __SCAN_ALGORITHM: ClassVar[str] = '-T4'
    __FOUND_HOST_MSG: ClassVar[str] = 'host is up'

    def __init__(self, settings: NMapDeviceDetectorSettings) -> None:
        """initialize nmap device detector

        Args:
            settings (NMapDeviceDetectorSettings): detector settings from yaml 
        """
        super().__init__()
        self.__stop_event = Event()
        self.__settings = settings
        self.__args: List[str] = [self.__NMAP_BIN, self.__SCAN_ALGORITHM, self.__SCAN_TYPE, self.__settings.ip_addr]
        self.__handler: Optional[Callable[[bool], None]] = None
        self.__thread: Optional[Thread] = None

    def init(self) -> None:
        """Dedicated (lazy) nmap device detector initialization, which checks if nmap binary is available 
        """
        LOGGER.info("Initializing nmap device detector")
        if not which(self.__NMAP_BIN):
            # check if nmap is available, otherwise raise error
            raise CamguardError(f"Couldn't find nmap binary: {self.__NMAP_BIN}")

    def register_handler(self, handler: Callable[[bool], None]) -> None:
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

        if not self.__thread:
            LOGGER.debug("Detector thread has never been started")
            return
        self.__stop_event.set()
        self.__thread.join(4 * self.__settings.interval_seconds)

        self.__stop_event.clear()
        self.__thread = None
        LOGGER.info("Shutdown successful")

    def __do_work(self):
        LOGGER.info("Starting device check thread")
        while not self.__stop_event.wait(self.__settings.interval_seconds):
            # check for device in network
            result = run(self.__args, capture_output=True, text=True) # skipcq: PYL-W1510
            # TODO: handle errors from cmd
            found_device = self.__FOUND_HOST_MSG in result.stdout.lower()

            if self.__handler:
                # call handler and notice about detection status
                self.__handler(found_device)

        LOGGER.info("Exiting device check thread")
