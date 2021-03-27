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
        # initialize class logger
        LOGGER.debug('Setting up camera and motion sensor')

        self.motion_detector: MotionDetector = MotionSensor(motion_sensor_gpio_pin)
        self.motion_handler: MotionHandler = PiCam(record_root_path)
        self.gdrive: GDriveStorage = GDriveStorage() if upload else None
        if self.gdrive:
            self.gdrive.authenticate()

    def guard(self):
        LOGGER.info("Start guard...")
        self.motion_detector.detect_motion(self.motion_handler)

    def shutdown(self):
        LOGGER.info('Shutting down camguard')
        # order has to be <1> handler <2> sensor
        self.motion_handler.shutdown()
        self.motion_detector.shutdown()
