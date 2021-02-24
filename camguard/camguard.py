import logging
import sys
from argparse import ArgumentParser
from signal import SIGINT, sigwait

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
        LOGGER.debug("Setting up camera and motion sensor")

        # import packages in here so that script execution can be run without them
        from camguard.motionsensor.motionsensor_facade import MotionSensorFacade
        from camguard.cam.cam_facade import CamFacade
        from camguard.gdrive.gdrive_facade import GDriveFacade

        self.motion_sensor = MotionSensorFacade(motion_sensor_gpio_pin)
        self.camera = CamFacade(record_root_path)
        self.gdrive = None
        if gdrive_upload:
            self.gdrive = GDriveFacade()

    def guard(self) -> None:
        """start guard...
        """

        if self.gdrive:
            self.gdrive.authenticate()

        self.motion_sensor.detect_motion(self._motion_handler)

    def shutdown(self) -> None:
        """
        shutdown the guard
        """
        LOGGER.info("Shutting down camguard")
        # order has to be <1> camera <2> motion_sensor
        self.camera.shutdown()
        self.motion_sensor.shutdown()
        sys.exit()

    def _motion_handler(self) -> None:
        LOGGER.info("Detected motion...")
        recorded_files = self.camera.record_picture()
        self.gdrive.upload(recorded_files)


def _parse_args():
    parser = ArgumentParser(
        description="A motion sensor controlled home surveillance system"
    )

    group_rec = parser.add_argument_group(title="Camguard surveillance",
                                          description="Detect motion with configured sensor "
                                                      "and record pictures")
    group_rec.add_argument("-l", "--log", type=str, default="INFO",
                           choices=["INFO", "DEBUG",
                                    "WARN", "ERROR", "CRITICAL"],
                           help="Define custom log level, default is INFO")
    group_rec.add_argument("record_path", metavar="PATH",
                           type=str, help="Root path for camera records")
    group_rec.add_argument("gpio_pin", metavar="PIN", type=int,
                           help="Raspberry GPIO motion sensor pin number")

    group_gauth = parser.add_argument_group(title="Optional Google-Drive upload",
                                            description="For using the Google-Drive upload, "
                                                        "please configure the Google-OAuth "
                                                        "authentication with the google-oauth setup")
    group_gauth.add_argument("-u", "--upload", default=False, metavar='',
                             help="Upload files to a configured google drive, "
                                  "authenticates on first usage")

    return parser.parse_args()


def _configure_logger(loglevel: str) -> None:
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        handlers=[logging.StreamHandler(
                        ), logging.FileHandler("camguard.log")],
                        level=loglevel)


def main() -> None:
    args = _parse_args()
    _configure_logger(args.log)

    LOGGER.info(f"Starting up with args: {args}")

    camguard = CamGuard(args.gpio_pin, args.record_path, args.upload)
    camguard.guard()

    print("Camguard running, press ctrl-c to quit...")
    sigwait((SIGINT,))
    camguard.shutdown()


if __name__ == "__main__":
    main()
