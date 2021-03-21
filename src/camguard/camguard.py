from camguard.picam import PiCam
from camguard.motion import MotionHandler, MotionDetector
from camguard.motion_sensor import MotionSensor
from camguard.gdrive_facade import GDriveFacade
import logging

LOGGER = logging.getLogger(__name__)


class CamGuard:
    """triggers picture record when motion sensor gets activated
    """

    def __init__(self, motion_sensor_gpio_pin: int, record_root_path: str, gdrive_upload: bool):
        """Camguard ctor

        Args:
            motion_sensor_gpio_pin (int): gpio pin for motion sensor
            record_root_path (str): root path for saving cam files
            gdrive_upload (bool): set to true for additionally using gdrive upload
        """
        # initialize class logger
        LOGGER.debug('Setting up camera and motion sensor')

        self.sensor: MotionDetector = MotionSensor(motion_sensor_gpio_pin)
        self.cam: MotionHandler = PiCam(record_root_path)
        self.gdrive: GDriveFacade = GDriveFacade() if gdrive_upload else None
        if self.gdrive:
            self.gdrive.authenticate()

    def guard(self):
        LOGGER.info("Start guard...")
        self.sensor.detect_motion(self.cam)

    def shutdown(self):
        LOGGER.info('Shutting down camguard')
        # order has to be <1> camera <2> motion_sensor <3> gdrive
        self.cam.shutdown()
        self.sensor.shutdown()
