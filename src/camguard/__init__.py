import logging
import time
from sys import stderr, stdout, exit
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from signal import SIGINT, SIGTERM, Signals, sigwait
from typing import Any, Dict, Optional

from daemon.daemon import DaemonContext  # type: ignore[reportMissingTypeStubs]
from pid import PidFile  # type: ignore[reportMissingTypeStubs]


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
                        help="Define custom config path, '~' and env variables will be resolved.")
    parser.add_argument("--daemonize", default=False, action="store_true", help="Run camguard as a unix daemon")
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
                        " - %(message)s", handlers=[logging.StreamHandler()], level=loglevel)
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
        camguard = CamGuard(args.config_path, args.upload)
        camguard.init()

        _run(args, camguard)
    except SystemExit as e:
        LOGGER.debug(e)
        LOGGER.info("Camguard shut down gracefully")
    except Exception as e:
        LOGGER.error("Unexpected error occured", exc_info=e)

    LOGGER.debug(f"Camguard exit with code: {rc}")
    exit(rc)
