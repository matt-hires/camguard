import logging
import time
from sys import stderr, stdout, exit
from argparse import ArgumentParser
from signal import SIGINT, SIGTERM

from daemon.daemon import DaemonContext
from pid import PidFile

__version__ = "1.1.0"
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
    group_rec.add_argument("-d", "--detach", default=False, action="store_true",
                           help="Detach process from current terminal "
                           "to run in the background as a daemon. "
                           "Redundant if the process is started by the init system "
                           "(sys-v, systemd, ...)")

    group_gdrive = parser.add_argument_group(title="Optional google-drive storage upload",
                                             description="For using the upload, "
                                             "please configure the Google-OAuth "
                                             "authentication with the google-oauth setup")
    group_gdrive.add_argument("-u", "--upload", default=False, action='store_true',
                              help="Upload files to a configured google drive, "
                              "authenticates on first usage")

    return parser.parse_args()


def _configure_logger(loglevel: str) -> None:
    logging.basicConfig(format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s"
                        " - %(message)s",
                        handlers=[logging.StreamHandler()],
                        level=loglevel)
    logging.logThreads = True


def _configure_daemon(detach: bool, camguard) -> DaemonContext:
    signal_map = {
        SIGTERM: lambda sig, tb: _shutdown_daemon(camguard, sig, tb),
        SIGINT: lambda sig, tb: _shutdown_daemon(camguard, sig, tb)
    }

    # setup pid file context (/var/run/camguard.pid)
    pid_file: PidFile = PidFile(pidname="camguard") if detach else None
    work_dir: str = '/' if detach else '.'

    return DaemonContext(detach_process=detach,
                         pidfile=pid_file,
                         signal_map=signal_map,
                         stderr=stderr,
                         stdout=stdout,
                         working_directory=work_dir)


def _shutdown_daemon(camguard, signal_number, stack_frame):
    LOGGER.info("Gracefully shutting down Camguard")
    if camguard:
        camguard.stop()
    raise SystemExit(f"Received shutdown signal: {signal_number}")


def main():
    try:
        rc = 0
        args = _parse_args()
        _configure_logger(args.log)

        LOGGER.info(f"Starting up with args: {args}")

        from camguard.camguard import CamGuard
        camguard = CamGuard(args.gpio_pin, args.record_path, args.upload)
        # init camguard before starting daemon context
        camguard.init()

        daemon_context: DaemonContext = _configure_daemon(args.detach, camguard)
        with daemon_context:
            camguard.start()
            if not args.detach:
                LOGGER.info("Camguard running, press ctrl-c to quit")

            # main loop
            while True:
                time.sleep(10)
    except SystemExit as e:
        LOGGER.debug(e)
        LOGGER.info("Camguard shut down gracefully")
        rc = 0
    except Exception as e:
        LOGGER.error(f"Unexpected error occured: {e}")

    LOGGER.debug(f"Camguard exit with code: {rc}")
    exit(rc)
