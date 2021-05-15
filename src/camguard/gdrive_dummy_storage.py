import logging
from time import sleep
from typing import List

from .bridge import FileStorageImpl
from .gdrive_storage import GDriveUploadManager

LOGGER = logging.getLogger(__name__)


class GDriveDummyStorage(FileStorageImpl):
    """dummy implementation for gdrive upload
    can be used for running camguard in a dummy mode 
    """
    _auth_sim_time: float = 1.0
    _upload_sim_time: float = 1.0

    def __init__(self) -> None:
        super().__init__()
        LOGGER.debug("Configuring gdrive dummy storage")
        self._daemon = GDriveUploadManager(GDriveDummyStorage.upload,
                                           queue_size=30)

    def authenticate(self) -> None:
        LOGGER.info(f"Simulating authentication (waiting {self._auth_sim_time} sec)")
        sleep(self._auth_sim_time)

    def start(self) -> None:
        self._daemon.start()

    def stop(self) -> None:
        self._daemon.stop()

    def enqueue_files(self, files: List[str]) -> None:
        """enqueue file paths for upload

        Args:
            files (List[str]): files to enqueue 
        """
        self._daemon.enqueue_files(files)

    @classmethod
    def upload(cls, file: str) -> None:
        LOGGER.info(f"Simulating upload (waiting {cls._upload_sim_time} sec)"
                    f"for: {file}")
        sleep(cls._upload_sim_time)
