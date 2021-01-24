import logging
import sys
from argparse import ArgumentParser
from signal import SIGINT, sigwait

LOGGER = logging.getLogger(__name__)


class CamGuard:
    """
    triggers picture record when motion sensor gets activated
    """

    def __init__(self, motion_sensor_gpio_pin: int, record_root_path: str):
        """
        default ctor
        :param motion_sensor_gpio_pin: gpio pin for motion sensor
        """
        # initialize class logger
        LOGGER.debug("Setting up camera and motion sensor")

        # import packages in here so that script execution can be run without them
        from camguard.motionsensor.motionsensor_adapter import MotionSensorAdapter
        from camguard.cam.cam_adapter import CamAdapter

        self.motion_sensor = MotionSensorAdapter(motion_sensor_gpio_pin)
        self.camera = CamAdapter(record_root_path)

    def guard(self) -> None:
        """
        start guard
        """
        self.motion_sensor.detect_motion(self._motion_handler)

    def shutdown(self) -> None:
        """
        shutdown the guard
        """
        LOGGER.info("Shutting down camguard, currently running recording will finish")
        # order has to be <1> camera <2> motion_sensor
        self.camera.shutdown()
        self.motion_sensor.shutdown()
        sys.exit()

    def _motion_handler(self) -> None:
        LOGGER.info("Detected motion...")
        self.camera.record_picture()


def _parse_args():
    parser = ArgumentParser(
        description="A motion sensor controlled home surveillance system"
    )

    parser.add_argument("-l", "--log", type=str, default="INFO", choices=["INFO", "DEBUG", "WARN", "ERROR", "CRITICAL"],
                        help="Define custom log level, default is INFO")
    parser.add_argument("record_path", metavar="PATH", type=str, help="Root path for camera records")
    parser.add_argument("gpio_pin", metavar="PIN", type=int, help="Raspberry GPIO motion sensor pin number")

    return parser.parse_args()


def _configure_logger(loglevel: str) -> None:
    # noinspection PyArgumentList
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler("camguard.log")],
                        level=loglevel)


def main() -> None:
    args = _parse_args()
    _configure_logger(args.log)

    LOGGER.info(f"Starting up with args: {args}")

    camguard = CamGuard(args.gpio_pin, args.record_path)
    camguard.guard()

    print("Camguard running, press ctrl-c to quit...")
    sigwait((SIGINT,))
    camguard.shutdown()


if __name__ == "__main__":
    main()
