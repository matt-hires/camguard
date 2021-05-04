import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from enum import Enum
from os import path
from queue import Empty, Full, Queue
from random import uniform
from threading import Event, Lock, Thread
from typing import Dict, List, Sequence

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
from pydrive.settings import InvalidConfigError

from camguard.bridge import FileStorageImpl

from .exceptions import ConfigurationError, GDriveError

LOGGER = logging.getLogger(__name__)


class GDriveMimetype(Enum):
    """google drive mimetype enumeration
    see https://developers.google.com/drive/api/v3/ref-export-formats for full listing
    """
    FOLDER = "application/vnd.google-apps.folder"
    JPEG = "image/jpeg"


class GDriveStorageAuth:
    """manages gdrive oauth authentication control
    """

    _gauth: GoogleAuth = None

    @classmethod
    def login(cls, settings_file: str = "google-oauth-settings.yaml") -> GoogleAuth:
        """login via cli

        Args:
            settings_file (str, optional): Google authentication settings file path. 
            Defaults to "google-oauth-settings.yaml".

        Raises:
            ConfigurationError: raises configuration error in case of missing secrets
        """
        if not cls._gauth:
            LOGGER.info("Authenticating to google")
            try:
                cls._gauth = GoogleAuth(settings_file=settings_file)
                cls._gauth.CommandLineAuth()
            except InvalidConfigError:
                raise ConfigurationError("Cannot find client_secrets.json")

        return cls._gauth


class GDriveUploadDaemon(Thread):
    """Daemon for handling gdrive upload workers
    filepath to uploaded are kept in a queue
    """
    _QUEUE_SIZE: int = 100
    _MAX_WORKERS: int = 3

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self._stop_event = Event()
        self._queue: Queue[str] = Queue(maxsize=GDriveUploadDaemon._QUEUE_SIZE)

    def enqueue_files(self, files: List[str]) -> None:
        """enqueue files for upload.

        Args:
            files (List[str]): path of the files to enqueue 
        """
        for file in files:
            self._enqueue_file(file)

    def _enqueue_file(self, file_path: str) -> None:
        LOGGER.debug(f"Enqueuing file: {file_path}")
        try:
            self._queue.put_nowait(file_path)
        except Full:
            LOGGER.warn(f"maxium queue length of "
                        f"{self._MAX_WORKERS} reached. Loosing item {file_path}")
            # TODO: handle full queue and exceptions
            pass

    def run(self) -> None:
        """start worker threads *and* wait for them to finish
        """
        self._stop_event.clear()
        LOGGER.info(f"Daemon starting up")
        # ThreadPoolExecutor ContextManager blocks till every worker is done
        with ThreadPoolExecutor(max_workers=self._MAX_WORKERS,
                                thread_name_prefix='UploadWorkerThread') as executor:
            for _ in range(self._MAX_WORKERS):
                executor.submit(self._upload_worker)

    def stop(self, timeout_sec: float = 10.0) -> None:
        """stop daemon thread gracefully

        Args:
            timeout_sec (float, optional): timeout seconds. Defaults to 10.0.

        Raises:
            GDriveError: if daemon failed to stop within timeout
        """
        if not self.is_alive():
            LOGGER.debug("Daemon has already been stopped")
            return

        LOGGER.info("Daemon shutting down gracefully")
        self._stop_event.set()
        self.join(timeout_sec)

        if self.is_alive():
            msg = f"Daemon failed to stop within {timeout_sec}"
            LOGGER.error(msg)
            raise GDriveError(msg)

    def _upload_worker(self) -> None:
        LOGGER.info("Init")

        try:
            # wait between 100ms...500ms for eventual stop
            while not self._stop_event.wait(round(uniform(0.1, 0.5), 1)):
                try:
                    file = self._queue.get_nowait()
                except Empty:
                    # queue is empty continue loop
                    continue

                try:
                    LOGGER.debug(f"Starting upload: {file}")
                    GDriveStorage.upload(file)
                    LOGGER.debug(f"Upload successful: {file}")
                except GDriveError as e:
                    LOGGER.warn(f"Upload failed: {file} with error: {e}")
                    # TODO: re-enqueue on error
                    # self._enqueue_file(file)
        except Exception as e:
            LOGGER.error(f"Unrecoverable error in upload worker: {e}")

        LOGGER.info("Finished")


class GDriveStorage(FileStorageImpl):
    """ Manages GDrive file upload
    """
    _lock = Lock()
    _gauth: GoogleAuth = None
    _upload_folder_title: str = "Camguard"

    def __init__(self):
        LOGGER.debug("Configuring gdrive storage")
        self._daemon: GDriveUploadDaemon = GDriveUploadDaemon()

    def authenticate(self) -> None:
        """authenticate to gdrive via cli
        """
        self.__class__._gauth = GDriveStorageAuth.login()

    def start(self) -> None:
        """start the upload daemon thread
        """
        self._daemon.start()

    def stop(self) -> None:
        """stop the upload daemon thread
        """
        self._daemon.stop()

    def enqueue_files(self, files: List[str]) -> None:
        """enqueue file paths for upload

        Args:
            files (List[str]): files to enqueue 
        """
        self._daemon.enqueue_files(files)

    @classmethod
    def upload(cls, file: str) -> None:
        """upload given file to gdrive

        Args:
            file (str): file to upload 

        Raises:
            GDriveError: on authentication failure
        """

        if not cls._gauth:
            raise GDriveError("GoogleDrive not authenticated")
        elif cls._gauth.access_token_expired:
            raise GDriveError("GoogleDrive authentication token expired")

        gdrive = GoogleDrive(cls._gauth)

        try:
            # mutex parent folder creation
            cls._lock.acquire()
            # create the root folder
            root_folder: GoogleDriveFile = cls._create_file(
                gdrive=gdrive,
                name=cls._upload_folder_title,
                mimetype=GDriveMimetype.FOLDER,
                parent_id='root')

            # create directory with the current date
            cur_date: str = date.today().strftime("%Y%m%d")
            date_folder: GoogleDriveFile = cls._create_file(
                gdrive=gdrive,
                name=cur_date,
                mimetype=GDriveMimetype.FOLDER,
                parent_id=root_folder['id']
            )
        finally:
            # release in any case
            cls._lock.release()

        # check if file path is a file with os.path.isfile
        file_name = path.basename(file)
        gdrive_file: GoogleDriveFile = cls._create_file(
            gdrive=gdrive,
            name=file_name,
            mimetype=GDriveMimetype.JPEG,
            parent_id=date_folder['id']
        )

        LOGGER.info("Uploading file: "
                    f"'{cls._upload_folder_title}/{cur_date}/{file_name}'")

        gdrive_file.SetContentFile(file)
        gdrive_file.Upload()

        LOGGER.info("Upload file finished: "
                    f"'{cls._upload_folder_title}/{cur_date}/{file_name}'")

    @classmethod
    def _create_file(cls, *, gdrive: GoogleDrive, name: str, mimetype: GDriveMimetype,
                     parent_id: str = None) -> GoogleDriveFile:
        """create file or folder on gdrive storage if it's not already existing

        Args:
            name (str): name of the file/folder to create
            mimetype (GDriveMimetype): mimetype for file or folder 
            parent_id (str, optional): parent where the file or folder should be 
            located in. Defaults to None.

        Raises:
            GDriveError: if multiple folders where found with the given name under 
            the given parent id

        Returns:
            GoogleDriveFile: representation of the created/found file  
        """
        existing: Sequence[GoogleDriveFile] = cls._search_file(gdrive=gdrive,
                                                               name=name,
                                                               parent_id=parent_id,
                                                               mimetype=mimetype)
        file: GoogleDriveFile = None
        if existing:
            if len(existing) > 1:
                raise GDriveError(f"Multiple files ('{name}') found under"
                                  f"given parent {parent_id}")

            file = existing[0]
            LOGGER.debug(f"Found existing file, name: '{name}', id: '{file['id']}', "
                         f"parent: '{parent_id}'")
        else:
            resource: Dict = {
                'title': name,
                'mimeType': mimetype.value
            }

            if parent_id:
                resource.update({
                    'parents': [{
                        'id': parent_id
                    }]
                })

            file = gdrive.CreateFile(resource)
            file.Upload()
            LOGGER.debug(f"Created file, name: '{name}', id: '{file['id']}', "
                         f"parent: '{parent_id}'")

        return file

    @classmethod
    def _search_file(cls, *, gdrive: GoogleDrive, name: str, mimetype: GDriveMimetype = None,
                     parent_id: str = None) -> Sequence[GoogleDriveFile]:
        """search for a file/folder on google drive with certain parameters

        Args:
            name (str): the human readable name of the file or folder
            mimetype (GDriveMimetype, optional): mimetype of the file to search.
            Defaults to None
            parent_id (str, optional): parent/folder id where the file is 
            located in. Defaults to None.

        Raises:
            ValueError: on empty file name

        Returns:
            GoogleDriveFileList: list representation of a google drive files 
        """
        if not name:
            raise ValueError("name not set")

        query: Dict = {
            'q': cls._build_query(title=name,
                                  mimetype=mimetype,
                                  parent_id=parent_id)
        }
        return gdrive.ListFile(query).GetList()

    @classmethod
    def _build_query(cls, *, title: str, mimetype: GDriveMimetype = None,
                     trashed: bool = False, parent_id: str = None) -> str:
        parent_filter = f"and '{parent_id}' in parents " if parent_id else ""
        mimetype_filter = f"and mimeType='{mimetype.value}' " if mimetype else ""

        return f"title='{title}' " \
            f"{mimetype_filter}" \
            f"{parent_filter}" \
            f"and trashed={str(trashed).lower()}"
