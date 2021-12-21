"""
init module of camguard, which supports:
* init, start and stop handling
* configuration of logging and cli arguments
* daemonized usage
"""

import logging
import sys
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from signal import SIGINT, SIGTERM, Signals, sigwait
from typing import Any, Dict, Optional

from daemon.daemon import DaemonContext  # type: ignore[reportMissingTypeStubs]
from pid import PidFile  # type: ignore[reportMissingTypeStubs]

from camguard.exceptions import \
    CamguardError  # type: ignore[reportMissingTypeStubs]

__version__ = '1.1.0-beta'
LOGGER = logging.getLogger(__name__)


def _parser() -> ArgumentParser:
    """creates argument parser for parsing arguments

    Returns:
        ArgumentParser: parser object
    """
    parser = ArgumentParser(
        prog=__name__,
        description="A motion sensor controlled home surveillance system",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)

    parser.add_argument('-l', type=str, default='INFO', dest='log',
                        choices=['INFO', 'DEBUG', 'WARN', 'ERROR', 'CRITICAL'],
                        help="Define custom log level")
    parser.add_argument('-c', metavar='CONFIG_PATH', type=str, default='$HOME/.config/camguard', dest='config_path',
                        help="Define custom config path, '~' and env variables will be resolved, "
                        "file name is 'settings.yaml'.")
    parser.add_argument('--daemonize', default=False, action='store_true', help="Run camguard as a unix daemon")
    parser.add_argument('--detach', default=False, action='store_true',
                        help="Detach process from current terminal "
                        "to run in the background as a daemon. Therefore this is "
                        "only useful when combined with --daemonize. "
                        "Redundant if the process is started by the init system "
                        "(sys-v, systemd, ...)")
    return parser


def __parse_args(parser: ArgumentParser) -> Namespace:
    """configures cli and parses arguments

    Returns:
        Namespace: as a simple object for storing arguments
    """
    args = parser.parse_args()

    if args.detach and not args.daemonize:
        LOGGER.warning("Ignoring --detach argument as it is used without --daemonize")

    return args


def __configure_logger(loglevel: str) -> None:
    """configures basic logging system

    Args:
        loglevel (str): given loglevel to configure, this is restricted by cli-args to: 
                        INFO, DEBUG, WARN, ERROR, CRITICAL
    """
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(threadName)s - %(name)s - %(message)s",
                        handlers=[logging.StreamHandler()], level=loglevel)
    logging.logThreads = True


def __shutdown(camguard: Optional[Any], signal_number: Signals) -> None:
    """handle shutdown of camguard/-daemon
    shutdown signal can be raised by cli (ctrl+c) or init-system in a daemon usage scenario (i.e. systemd)

    Args:
        camguard (Optional[Any]): camguard instance which has been started, could be 
        signal_number (Signals): system signal which has been raised 

    Raises:
        SystemExit: for shutting down camguard 
    """

    LOGGER.info("Gracefully shutting down Camguard")
    if camguard:
        camguard.stop()
    raise SystemExit(f"Received shutdown signal: {signal_number}")


def __configure_daemon(detach: bool, camguard: Any) -> DaemonContext:
    """in case of running daemonized, this configures daemon as described in PEP 3143

    Args:
        detach (bool): set to true to detach from terminal 
        camguard (Any): the camguard instance to run 

    Returns:
        DaemonContext: daemon context which handles turning program into a daemon process
    """
    signal_map: Dict[Signals, Any] = {
        # lambda type couldn't be inferred
        SIGTERM: lambda sig, _: __shutdown(camguard, sig),  # type: ignore
        SIGINT: lambda sig, _: __shutdown(camguard, sig)  # type: ignore
    }

    # setup pid file context (/var/run/camguard.pid)
    pid_file: Optional[PidFile] = PidFile(pidname='camguard') if detach else None
    work_dir: str = '/' if detach else '.'

    return DaemonContext(detach_process=detach,
                         pidfile=pid_file,
                         signal_map=signal_map,
                         stderr=sys.stderr,
                         stdout=sys.stdout,
                         working_directory=work_dir)


def __run_daemonized(args: Namespace, camguard: Any) -> None:
    """in case of running daemonized, this configures the daemon and starts camguard in background,
     while staying in a main loop

    Args:
        args (Namespace): argument storage object which is returned from parsing arguments
        camguard (Any): the camguard instance to run 
    """
    daemon_context: DaemonContext = __configure_daemon(args.detach, camguard)
    with daemon_context:
        camguard.start()
        if not args.detach:
            LOGGER.info("Camguard running, press ctrl-c to quit")

        # main loop
        while True:
            time.sleep(1.0)


def __init(camguard: Any) -> bool:
    """initialize camguard and its equipment before start, automatically stops if an error occurs

    Args:
        camguard (Any): camguard instance to run

    Returns:
        bool: True on success, otherwise False
    """
    success = False
    try:
        camguard.init()
        success = True
    except CamguardError as e:
        LOGGER.exception(f"Error during initialization: {e.message}", exc_info=e)
        camguard.stop()  # in case a component already started a thread in init (DummyGpioSensor)
    # skipcq: PYL-W0703
    except Exception as e:
        LOGGER.exception("Error during initialization", exc_info=e)
        camguard.stop()  # in case a component already started a thread in init (DummyGpioSensor)

    return success


def __run(args: Namespace, camguard: Any) -> None:
    """Runs camguard as program or daemonized process.
    Shutdown is done by handling SystemExit exception.

    Args:
        args (Namespace): argument storage object, which is returned from parsing arguments
        camguard (Any): camguard instance to run

    """
    if args.daemonize:
        return __run_daemonized(args, camguard)

    camguard.start()
    LOGGER.info("Camguard running, press ctrl-c to quit")
    sigwait((SIGINT,))
    __shutdown(camguard, SIGINT)


def main() -> int:
    """main entry point of camguard.
    parses cli args, configures logging and handles startup
    """
    rc: int = 1
    try:
        args = __parse_args(_parser())
        __configure_logger(args.log)

        LOGGER.info(f"Starting up with args: {args}")

        from camguard.camguard import Camguard
        _camguard = Camguard(args.config_path)

        # run camguard if it was successfully initialized
        if __init(_camguard):
            __run(args, _camguard)
    except SystemExit as sysEx:
        LOGGER.debug(f"Shut down by system exit: {str(sysEx)}")
        LOGGER.info("Camguard shut down gracefully")
        rc = 0
    # skipcq: PYL-W0703
    except Exception as ex:
        LOGGER.exception("Unexpected error occurred", exc_info=ex)

    LOGGER.debug(f"Camguard exit with code: {rc}")
    return rc
