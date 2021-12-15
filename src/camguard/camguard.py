import logging
from typing import Any, Generator, List, Optional

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
        self.__init = False
        self.__config_path = config_path
        self.__settings: CamguardSettings = CamguardSettings.load_settings(self.__config_path)

        self.__detector = MotionDetector(self.__config_path)
        self.__handler = MotionHandler(self.__config_path)
        self.__file_storage: Optional[FileStorage] = None
        self.__mail_client: Optional[MailClient] = None
        self.__netw_dev_detector: Optional[NetworkDeviceDetector] = None

    def init(self):
        """initialize equipment, this *has* to be done before start
        """
        LOGGER.info("Initializing equipment")

        if ComponentsType.FILE_STORAGE in self.__settings.components:
            LOGGER.info("Setting up file storage")
            self.__file_storage = FileStorage(self.__config_path)
            self.__file_storage.authenticate()
            self.__file_storage.start()

        if ComponentsType.MAIL_CLIENT in self.__settings.components:
            LOGGER.info("Setting up mail client")
            self.__mail_client = MailClient(self.__config_path)

        if ComponentsType.NETWORK_DEVICE_DETECTOR in self.__settings.components:
            LOGGER.info("Setting up network device dector")
            self.__netw_dev_detector = NetworkDeviceDetector(self.__config_path)
            self.__netw_dev_detector.register_handler(self.__detector.on_disable)

        self.__init = True

    def start(self):
        """start camguard

        Raises:
            CamguardError: is camguard hasn't been initialized
        """
        if not self.__init:
            raise CamguardError("Components have not been initialized successfully before start")

        if ComponentsType.NETWORK_DEVICE_DETECTOR in self.__settings.components and self.__netw_dev_detector:
            self.__netw_dev_detector.start()

        LOGGER.info("Starting camguard")

        # build handler pipe
        on_motion_pipe: List[Generator[None, Any, None]] = []

        if ComponentsType.FILE_STORAGE in self.__settings.components and self.__file_storage:
            on_motion_pipe.append(self.__file_storage.enqueue_files()) 

        if ComponentsType.MAIL_CLIENT in self.__settings.components and self.__mail_client:
            on_motion_pipe.append(self.__mail_client.send_mail())

        self.__detector.register_handlers([self.__handler.on_motion(on_motion_pipe)])

    def stop(self):
        """stop camguard
        """
        LOGGER.info("Stopping camguard")
        self.__handler.stop()
        self.__detector.stop()

        if ComponentsType.FILE_STORAGE in self.__settings.components and self.__file_storage:
            self.__file_storage.stop()

        if ComponentsType.NETWORK_DEVICE_DETECTOR in self.__settings.components and self.__netw_dev_detector:
            self.__netw_dev_detector.stop()

        self.__init = False
