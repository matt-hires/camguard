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

        # import packages in here so that script execution can be run without them
        from camguard.cam_facade import CamFacade
        from camguard.gdrive_facade import GDriveFacade
        from camguard.motionsensor_facade import MotionSensorFacade

        self.motion_sensor = MotionSensorFacade(motion_sensor_gpio_pin)
        self.camera = CamFacade(record_root_path)
        self.gdrive = GDriveFacade() if gdrive_upload else None

    def guard(self):
        """start guard...
        """
        LOGGER.info("Start guard...")
        if self.gdrive:
            self.gdrive.authenticate()

        self.motion_sensor.detect_motion(self._motion_handler)

    def shutdown(self):
        """ shutdown the guard
        """
        LOGGER.info('Shutting down camguard')
        # order has to be <1> camera <2> motion_sensor
        self.camera.shutdown()
        self.motion_sensor.shutdown()

    def _motion_handler(self):
        LOGGER.info('Detected motion...')
        recorded_files = self.camera.record_picture()
        if self.gdrive:
            self.gdrive.upload(recorded_files)
