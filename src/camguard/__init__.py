import logging
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from signal import SIGINT, SIGTERM, Signals, sigwait
from sys import exit, stderr, stdout
from typing import Any, Dict, Optional

from daemon.daemon import DaemonContext  # type: ignore[reportMissingTypeStubs]
from pid import PidFile  # type: ignore[reportMissingTypeStubs]

from camguard.exceptions import \
    CamGuardError  # type: ignore[reportMissingTypeStubs]

__version__ = "1.1.0"
LOGGER = logging.getLogger(__name__)


def _parse_args() -> Namespace:
    parser = ArgumentParser(
        prog=__name__,
        description="A motion sensor controlled home surveillance system",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)

    parser.add_argument("-l", type=str, default="INFO", dest='log',
                        choices=["INFO", "DEBUG", "WARN", "ERROR", "CRITICAL"],
                        help="Define custom log level")
    parser.add_argument("-c", metavar="CONFIG_PATH", type=str, default="$HOME/.config/camguard", dest="config_path",
                        help="Define custom config path, '~' and env variables will be resolved, "
                        "file name is 'settings.yaml'.")
    parser.add_argument("--daemonize", default=False, action="store_true", help="Run camguard as a unix daemon")
    parser.add_argument("--detach", default=False, action="store_true",
                        help="Detach process from current terminal "
                        "to run in the background as a daemon. Therefore this is "
                        "only useful when combined with --daemonize. "
                        "Redundant if the process is started by the init system "
                        "(sys-v, systemd, ...)")
    args = parser.parse_args()

    if args.detach and not args.daemonize:
        LOGGER.warn("Ignoring --detach argument as it is used without --daemonize")

    return args


def _configure_logger(loglevel: str) -> None:
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(threadName)s - %(name)s - %(message)s",
                        handlers=[logging.StreamHandler()], level=loglevel)
    logging.logThreads = True


def _configure_daemon(detach: bool, camguard: Any) -> DaemonContext:
    signal_map: Dict[Signals, Any] = {
        # lambda type couldn't be inferred
        SIGTERM: lambda sig, tb: _shutdown(camguard, sig, tb),  # type: ignore
        SIGINT: lambda sig, tb: _shutdown(camguard, sig, tb)  # type: ignore
    }

    # setup pid file context (/var/run/camguard.pid)
    pid_file: Optional[PidFile] = PidFile(pidname="camguard") if detach else None
    work_dir: str = '/' if detach else '.'

    return DaemonContext(detach_process=detach,
                         pidfile=pid_file,
                         signal_map=signal_map,
                         stderr=stderr,
                         stdout=stdout,
                         working_directory=work_dir)


def _shutdown(camguard: Any, signal_number: Signals, stack_frame: Any) -> None:
    LOGGER.info("Gracefully shutting down Camguard")
    if camguard:
        camguard.stop()
    raise SystemExit(f"Received shutdown signal: {signal_number}")


def _run_daemonized(args: Namespace, camguard: Any) -> None:
    daemon_context: DaemonContext = _configure_daemon(args.detach, camguard)
    with daemon_context:
        camguard.start()
        if not args.detach:
            LOGGER.info("Camguard running, press ctrl-c to quit")

        # main loop
        while True:
            time.sleep(1.0)


def _init(camguard: Any) -> bool:
    success = False
    try:
        camguard.init()
        success = True
    except CamGuardError as e:
        LOGGER.exception(f"Error during initialization: {e.message}", exc_info=e)
        camguard.stop()  # in case a component already started a thread in init (DummyGpioSensor)
    except Exception as e:
        LOGGER.exception(f"Error during initialization", exc_info=e)
        camguard.stop()  # in case a component already started a thread in init (DummyGpioSensor)

    return success


def _run(args: Namespace, camguard: Any) -> None:
    if args.daemonize:
        return _run_daemonized(args, camguard)

    camguard.start()
    LOGGER.info("Camguard running, press ctrl-c to quit")
    sigwait((SIGINT,))
    _shutdown(camguard, SIGINT, None)


def main():
    rc: int = 0
    try:
        args = _parse_args()
        _configure_logger(args.log)

        LOGGER.info(f"Starting up with args: {args}")

        from .camguard import CamGuard
        _camguard = CamGuard(args.config_path)

        # run camguard if it was successfully initialized
        if _init(_camguard):
            _run(args, _camguard)

    except SystemExit as e:
        LOGGER.debug(e)
        LOGGER.info("Camguard shut down gracefully")
    except Exception as e:
        LOGGER.exception("Unexpected error occured", exc_info=e)

    LOGGER.debug(f"Camguard exit with code: {rc}")
    exit(rc)
