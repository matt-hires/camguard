from camguard.exceptions import CamGuardError
from camguard.picam import PiCam
from camguard.motion import MotionHandler, MotionDetector
from camguard.motion_sensor import MotionSensor
from camguard.gdrive_storage import GDriveStorage
import logging

LOGGER = logging.getLogger(__name__)


class CamGuard:
    """triggers picture record when motion sensor gets activated
    """

    def __init__(self, motion_sensor_gpio_pin: int, record_root_path: str, upload: bool):
        """Camguard ctor

        Args:
            motion_sensor_gpio_pin (int): gpio pin for motion sensor
            record_root_path (str): root path for saving cam files
            upload (bool): set to true for additionally using gdrive upload
        """
        self._motion_sensor_gpio_pin = motion_sensor_gpio_pin
        self._record_root_path = record_root_path
        self._upload = upload
        self._motion_detector = None
        self._motion_handler = None

    def guard(self):
        if self._motion_detector or self._motion_handler:
            raise CamGuardError("Guard is already running")

        LOGGER.debug('Setting up camera and motion sensor')
        self._motion_detector: MotionDetector = MotionSensor(self._motion_sensor_gpio_pin)
        self._motion_handler: MotionHandler = PiCam(self._record_root_path)
        self.gdrive: GDriveStorage = GDriveStorage() if self._upload else None
        if self.gdrive:
            self.gdrive.authenticate()

        LOGGER.info("Starting guard")
        self._motion_detector.detect_motion(self._motion_handler)

    def shutdown(self):
        LOGGER.info('Shutting down camguard')
        # order has to be <1> handler <2> sensor
        if self._motion_handler:
            self._motion_handler.shutdown()
            self._motion_handler = None

        if self._motion_detector:
            self._motion_detector.shutdown()
            self._motion_detector = None
