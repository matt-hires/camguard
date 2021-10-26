import logging
from time import sleep
from typing import ClassVar, List

from camguard.file_storage_settings import DummyGDriveStorageSettings

from camguard.bridge_impl import FileStorageImpl
from camguard.gdrive_storage import GDriveUploadManager

LOGGER = logging.getLogger(__name__)


class DummyGDriveStorage(FileStorageImpl):
    """dummy implementation for gdrive upload
    can be used for running camguard in a dummy mode 
    """
    _AUTH_SIM_TIME: ClassVar[float] = 1.0
    _UPLOAD_SIM_TIME: ClassVar[float] = 1.0
    _id: ClassVar[int] = 0

    def __init__(self, settings: DummyGDriveStorageSettings) -> None:
        self._daemon = GDriveUploadManager(DummyGDriveStorage.upload, queue_size=30)
        self._settings = settings
        DummyGDriveStorage._id += 1

    def authenticate(self) -> None:
        LOGGER.info(f"Simulating authentication (waiting {self._AUTH_SIM_TIME} sec)")
        sleep(self._AUTH_SIM_TIME)

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

    @property
    def id(self) -> int:
        return DummyGDriveStorage._id

    @classmethod
    def upload(cls, file: str) -> None:
        LOGGER.info(f"Simulating upload (waiting {cls._UPLOAD_SIM_TIME} sec)"
                    f"for: {file}")
        sleep(cls._UPLOAD_SIM_TIME)
