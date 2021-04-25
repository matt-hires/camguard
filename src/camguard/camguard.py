from typing import List
from camguard.exceptions import CamGuardError
from camguard.picam import PiCam
from camguard.motion import MotionHandler, MotionDetector
from camguard.motion_sensor import MotionSensor
from camguard.gdrive_storage import GDriveStorageAuth, GDriveUploadDaemon
import logging

LOGGER = logging.getLogger(__name__)


class CamGuard:
    """triggers picture record when motion sensor gets activated
    """

    def __init__(self, motion_sensor_gpio_pin: int, record_root_path: str,
                 gdrive_auth: GDriveStorageAuth = None):
        """Camguard ctor

        Args:
            motion_sensor_gpio_pin (int): gpio pin for motion sensor
            record_root_path (str): root path for saving cam files
            gdrive_auth (GDriveStorageAuth, optional): set to gdrive authentication 
            object for uploading files to gdrive
        """
        self._motion_sensor_gpio_pin = motion_sensor_gpio_pin
        self._record_root_path = record_root_path
        self._motion_detector: MotionDetector = None
        self._motion_handler: MotionHandler = None
        self._gdrive_daemon: GDriveUploadDaemon = None
        self._gdrive_storage_auth: GDriveStorageAuth = gdrive_auth

    def start_guard(self):
        """start camguard with motion detector, handler and optional gdrive daemon

        Raises:
            CamGuardError: if guard is already running 
        """
        if self._motion_detector or self._motion_handler:
            raise CamGuardError("Guard is already running")

        LOGGER.info("Starting camguard")
        LOGGER.debug('Setting up camera and motion sensor')
        self._motion_detector: MotionDetector = MotionSensor(self._motion_sensor_gpio_pin)
        self._motion_handler: MotionHandler = PiCam(self._record_root_path)

        self._init_gdrive_daemon()

        self._motion_detector.detect_motion(self._motion_handler)

    def _init_gdrive_daemon(self):
        if not self._gdrive_storage_auth:
            return

        LOGGER.info("Setting up gdrive storage")
        self._gdrive_daemon = GDriveUploadDaemon(self._gdrive_storage_auth)
        self._gdrive_daemon.start()
        self._motion_handler.on_motion_finished = self._gdrive_daemon.enqueue_files

    def stop_guard(self):
        """stop camguard with handler, detector and optional gdrive daemon

        """
        LOGGER.info('Stopping camguard')
        if self._motion_handler:
            self._motion_handler.shutdown()
            self._motion_handler = None

        if self._gdrive_daemon:
            self._gdrive_daemon.stop()
            self._gdrive_daemon = None

        if self._motion_detector:
            self._motion_detector.shutdown()
            self._motion_detector = None
