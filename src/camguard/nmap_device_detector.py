import logging
import threading
from shutil import which
from subprocess import run
from threading import Event
from typing import Callable, ClassVar, List

from camguard.bridge_impl import NetworkDeviceDetectorImpl
from camguard.exceptions import ConfigurationError
from camguard.network_device_detector_settings import \
    NMapDeviceDetectorSettings

LOGGER = logging.getLogger(__name__)


class NMapDeviceDetector(NetworkDeviceDetectorImpl):
    _NMAP_BIN: ClassVar[str] = 'nmap'
    _SCAN_TYPE: ClassVar[str] = '-sn'
    _SCAN_ALGORHITHM: ClassVar[str] = '-T4'
    _FOUND_HOST_MSG: ClassVar[str] = 'host is up'

    def __init__(self, settings: NMapDeviceDetectorSettings) -> None:
        super().__init__()
        self._stop_event = Event()
        self._settings = settings
        self._args: List[str] = [self._NMAP_BIN, self._SCAN_ALGORHITHM, self._SCAN_TYPE, self._settings.ip_addr]

    def init(self) -> None:
        LOGGER.info("Initializing nmap device detector")
        if not which(self._NMAP_BIN):
            # check if nmap is available, otherwise raise error
            raise ConfigurationError(f"Couldn't find nmap binary: {self._NMAP_BIN}")

    def register_handler(self, handler: Callable[[bool], None]) -> None:
        LOGGER.debug("Registering nmap device detector callback")
        # skipcq: PYL-W0201
        self._handler = handler

    def start(self) -> None:
        LOGGER.info("Starting detector thread")
        # skipcq: PYL-W0201
        self._thread = threading.Thread(target=self._do_work)
        self._thread.start()

    def stop(self) -> None:
        LOGGER.info("Stopping detector thread")
        # stop check thread
        if not hasattr(self, '_thread') or not self._thread:
            LOGGER.debug("Detector thread has never been started")
            return
        self._stop_event.set()
        self._thread.join(4 * self._settings.interval_seconds)

        self._stop_event.clear()
        LOGGER.info("Shutdown successful")

    def _do_work(self):
        LOGGER.info("Starting device check thread")
        while not self._stop_event.wait(self._settings.interval_seconds):
            # check for device in network
            result = run(self._args, capture_output=True, text=True)
            # TODO: handle errors from cmd
            found_device = self._FOUND_HOST_MSG in result.stdout.lower()

            if hasattr(self, '_handler') and self._handler:
                # call handler and notice about detection status
                self._handler(found_device)

        LOGGER.info("Exiting device check thread")
