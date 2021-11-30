import logging
from typing import Any, Generator, List

from camguard.bridge_api import (FileStorage, MailClient, MotionDetector,
                                 MotionHandler, NetworkDeviceDetector)
from camguard.camguard_settings import CamguardSettings, ComponentsType
from camguard.exceptions import CamguardError

LOGGER = logging.getLogger(__name__)


class Camguard:
    """Camguard main device class, holds and manages equipment
    """

    def __init__(self, config_path: str):
        """create camguard instance

        Args:
            config_path (str): folder path where to read configuration files from
        """
        self._init = False
        self._config_path = config_path
        self._settings: CamguardSettings = CamguardSettings.load_settings(self._config_path)

        self._detector = MotionDetector(self._config_path)
        self._handler = MotionHandler(self._config_path)

    # skipcq: PYL-W0201
    def init(self):
        """initialize equipment, this *has* to be done before start
        """
        LOGGER.info("Initializing equipment")

        if ComponentsType.FILE_STORAGE in self._settings.components:
            LOGGER.info("Setting up file storage")
            self._file_storage = FileStorage(self._config_path)
            self._file_storage.authenticate()
            self._file_storage.start()

        if ComponentsType.MAIL_CLIENT in self._settings.components:
            LOGGER.info("Setting up mail client")
            self._mail_client = MailClient(self._config_path)

        if ComponentsType.NETWORK_DEVICE_DETECTOR in self._settings.components:
            LOGGER.info("Setting up network device dector")
            self._netw_dev_detector = NetworkDeviceDetector(self._config_path)
            self._netw_dev_detector.register_handler(self._detector.set_disabled)
            self._netw_dev_detector.start()

        self._init = True

    def start(self):
        """start camguard

        Raises:
            CamguardError: is camguard hasn't been initialized
        """
        if not self._init:
            raise CamguardError("Components have not been initialized successfully before start")

        LOGGER.info("Starting camguard")

        # build handler pipe
        on_motion_pipe: List[Generator[None, Any, None]] = []

        if ComponentsType.FILE_STORAGE in self._settings.components:
            on_motion_pipe.append(self._file_storage.enqueue_files()) 

        if ComponentsType.MAIL_CLIENT in self._settings.components:
            on_motion_pipe.append(self._mail_client.send_mail())

        self._detector.register_handlers([self._handler.on_motion(on_motion_pipe)])

    def stop(self):
        """stop camguard
        """
        LOGGER.info("Stopping camguard")
        self._handler.stop()
        self._detector.stop()

        if ComponentsType.FILE_STORAGE in self._settings.components:
            self._file_storage.stop()

        if ComponentsType.NETWORK_DEVICE_DETECTOR in self._settings.components:
            self._netw_dev_detector.stop()

        self._init = False
