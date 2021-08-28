import logging

from camguard.exceptions import CamGuardError

from camguard.bridge_api import FileStorage, MailClient, MotionDetector, MotionHandler

LOGGER = logging.getLogger(__name__)


class CamGuard:
    """CamGuard main device class, holds and manages equipment
    """

    def __init__(self, config_path: str, upload: bool):
        """Camguard ctor

        Args:
            config_path (str): folder path where to read configuration files from
            gpio_pin (int): raspi gpio pin for motion detection
            upload (bool): upload files to file storage (i.e. gdrive) 
        """
        self._init = False
        self._config_path = config_path
        self._detector = MotionDetector(self._config_path)
        self._handler = MotionHandler(self._config_path)
        self._mail_client = MailClient(self._config_path)
        self._upload = upload

    def init(self):
        """initialize equipment, this *has* to be done before start
        """
        LOGGER.info("Initializing equipment")

        if self._upload:
            LOGGER.info("Setting up file storage")
            self._file_storage = FileStorage(self._config_path)
            self._file_storage.authenticate()
            self._file_storage.start()

        self._init = True

    def start(self):
        """start camguard

        Raises:
            CamGuardError: is camguard hasn't been initialized
        """
        if not self._init:
            raise CamGuardError("Equipment has not been initialized before start")

        LOGGER.info("Starting camguard")

        # build handler pipeline
        if self._upload:
            _pipeline = [
                self._handler.on_motion([                # 1. trigger handler
                    self._file_storage.enqueue_files(),  # 2. enqueue files to upload
                    self._mail_client.send_mail()        # 3. send notification mail
                ])
            ]
        else:
            _pipeline = [
                self._handler.on_motion([           # 1. trigger handler
                    self._mail_client.send_mail()   # 2. send notification mail
                ]) 
            ]

        self._detector.register_handlers(_pipeline)

    def stop(self):
        """stop camguard
        """
        LOGGER.info('Stopping camguard')
        self._handler.stop()
        self._detector.stop()

        if self._upload:
            self._file_storage.stop()

        self._init = False
