import logging
from random import uniform, random
from threading import Event
import threading
from typing import Callable
from camguard.bridge_impl import NetworkDeviceDetectorImpl
from camguard.network_device_detector_settings import DummyNetworkDeviceDetectorSettings

LOGGER = logging.getLogger(__name__)


class DummyNetworkDeviceDetector(NetworkDeviceDetectorImpl):
    """simulation network device detection in a random interval between two boundaries
    """

    def __init__(self, settings: DummyNetworkDeviceDetectorSettings) -> None:
        super().__init__()
        self._stop_event = Event()
        self._settings = settings
        self._min_detection_seconds = 10.0 
        self._max_detection_seconds = 20.0

    def init(self) -> None:
        LOGGER.info("Initializing nmap device detector")

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
        self._thread.join(4 * self._max_detection_seconds)

        self._stop_event.clear()
        LOGGER.info("Shutdown successful")

    def _do_work(self):
        LOGGER.info("Starting device check thread")
        while not self._stop_event.wait(round(uniform(self._min_detection_seconds,
                                                      self._max_detection_seconds), 1)):
            # check for device in network
            LOGGER.debug("Simulating device detection")

            # randomize found device
            found_device: bool = bool(round(random()))

            if hasattr(self, '_handler') and self._handler:
                # call handler and notice about detection status
                self._handler(found_device)

        LOGGER.info("Exiting device check thread")
