from camguard.bridge import FileStorage, MotionHandler, MotionDetector
import logging
from camguard.exceptions import CamGuardError

from camguard.settings import MotionDetectorSettings, MotionHandlerSettings

LOGGER = logging.getLogger(__name__)


class CamGuard:
    """CamGuard main device class, holds and manages equipment
    """

    def __init__(self, gpio_pin: int, record_root_path: str, upload: bool):
        """Camguard ctor

        Args:
            gpio_pin (int): raspi gpio pin for motion detection
            record_root_path (str): root path for saving cam files
            upload (bool, optional): upload files to file storage (i.e. gdrive) 
        """
        self._init = False
        self._detector = MotionDetector(gpio_pin)
        self._handler = MotionHandler(record_root_path)
        self._file_storage = FileStorage() if upload else None

    def init(self):
        """initialize equipment
        this *has* to be done before start
        """
        LOGGER.info("Initializing equipment")

        self._handler.init()
        self._detector.init()

        if self._file_storage:
            LOGGER.info("Setting up file storage")
            self._file_storage.authenticate()
            self._file_storage.start()

        self._init = True

    def start(self):
        """start camguard

        Raises:
            CamGuardError: is camguard hasn't been initialized
        """
        if not self._init:
            raise CamGuardError("Equipment has not been initialized before start")

        LOGGER.info("Starting camguard")
        if self._file_storage:
            self._handler.after_handling(self._file_storage.enqueue_files)
        self._detector.on_motion(self._handler.handle_motion)

    def stop(self):
        """stop camguard
        """
        LOGGER.info('Stopping camguard')
        self._handler.stop()
        self._detector.stop()

        if self._file_storage:
            self._file_storage.stop()

        self._init = False
