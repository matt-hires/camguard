import logging
import sys
from argparse import ArgumentParser
from signal import SIGINT, sigwait

from .camguard import CamGuard

__version__ = "1.0.0"
LOGGER = logging.getLogger(__name__)


def _parse_args():
    parser = ArgumentParser(
        prog=__name__,
        description="A motion sensor controlled home surveillance system"
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)

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
    group_gauth.add_argument("-u", "--upload", default=False, action='store_true',
                             help="Upload files to a configured google drive, "
                                  "authenticates on first usage")

    return parser.parse_args()


def _configure_logger(loglevel: str):
    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        handlers=[logging.StreamHandler(
                        ), logging.FileHandler("camguard.log")],
                        level=loglevel)


def main():
    rc = 1
    try:
        args = _parse_args()
        _configure_logger(args.log)

        LOGGER.info(f"Starting up with args: {args}")

        camguard = CamGuard(args.gpio_pin, args.record_path, args.upload)
        camguard.guard()

        print("Camguard running, press ctrl-c to quit...")
        sigwait((SIGINT,))
        camguard.shutdown()
        rc = 0
    except Exception as e:
        print('Error: %s' % e, file=sys.stderr)
    sys.exit(rc)
