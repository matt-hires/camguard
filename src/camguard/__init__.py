import logging
import time
from sys import stderr, stdout, exit
from argparse import ArgumentParser, Namespace
from signal import SIGINT, SIGTERM, signal, sigwait

from daemon.daemon import DaemonContext
from pid import PidFile

__version__ = "1.1.0"
LOGGER = logging.getLogger(__name__)


def _parse_args() -> Namespace:
    parser = ArgumentParser(
        prog=__name__,
        description="A motion sensor controlled home surveillance system"
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)

    parser.add_argument("-l", type=str, default="INFO", dest='log',
                        choices=["INFO", "DEBUG",
                                 "WARN", "ERROR", "CRITICAL"],
                        help="Define custom log level, default is INFO")
    parser.add_argument("record_path", metavar="PATH",
                        type=str, help="Root path for camera records")
    parser.add_argument("gpio_pin", metavar="PIN", type=int,
                        help="Raspberry GPIO motion sensor pin number")
    parser.add_argument("--daemonize", default=False, action="store_true",
                        help="Run camguard as a unix daemon")
    parser.add_argument("--detach", default=False, action="store_true",
                        help="Detach process from current terminal "
                        "to run in the background as a daemon. Therefore this is "
                        "only useful when combined with --daemonize. "
                        "Redundant if the process is started by the init system "
                        "(sys-v, systemd, ...)")
    parser.add_argument("--upload", default=False, action='store_true',
                        help="Upload files to a configured google drive. "
                        "Authenticates on first usage.")

    args = parser.parse_args()

    if args.detach and not args.daemonize:
        LOGGER.warn("Ignoring --detach argument as it is used without --daemonize")

    return args


def _configure_logger(loglevel: str) -> None:
    logging.basicConfig(format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s"
                        " - %(message)s",
                        handlers=[logging.StreamHandler()],
                        level=loglevel)
    logging.logThreads = True


def _configure_daemon(detach: bool, camguard) -> DaemonContext:
    signal_map = {
        SIGTERM: lambda sig, tb: _shutdown(camguard, sig, tb),
        SIGINT: lambda sig, tb: _shutdown(camguard, sig, tb)
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


def _shutdown(camguard, signal_number: int, stack_frame) -> None:
    LOGGER.info("Gracefully shutting down Camguard")
    if camguard:
        camguard.stop()
    raise SystemExit(f"Received shutdown signal: {signal_number}")


def _run_daemonized(args: Namespace, camguard) -> None:
    daemon_context: DaemonContext = _configure_daemon(args.detach, camguard)
    with daemon_context:
        camguard.start()
        if not args.detach:
            LOGGER.info("Camguard running, press ctrl-c to quit")

        # main loop
        while True:
            time.sleep(1.0)


def _run(args: Namespace, camguard) -> None:
    if args.daemonize:
        return _run_daemonized(args, camguard)

    camguard.start()
    LOGGER.info("Camguard running, press ctrl-c to quit")
    sigwait((SIGINT,))
    _shutdown(camguard, SIGINT, None)


def main():
    try:
        rc = 0
        args = _parse_args()
        _configure_logger(args.log)

        LOGGER.info(f"Starting up with args: {args}")

        from camguard.camguard import CamGuard
        camguard = CamGuard(args.gpio_pin, args.record_path, args.upload)
        camguard.init()

        _run(args, camguard)
    except SystemExit as e:
        LOGGER.debug(e)
        LOGGER.info("Camguard shut down gracefully")
        rc = 0
    except Exception as e:
        LOGGER.error("Unexpected error occured", exc_info=e)

    LOGGER.debug(f"Camguard exit with code: {rc}")
    exit(rc)
