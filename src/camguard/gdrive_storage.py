import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from enum import Enum
from os import path
from queue import Empty, Full, Queue
from random import uniform
from threading import Event, Lock
from typing import Callable, ClassVar, List, Optional, Sequence

from pydrive.auth import GoogleAuth  # type: ignore
from pydrive.drive import GoogleDrive  # type: ignore
from pydrive.files import GoogleDriveFile  # type: ignore
from pydrive.settings import InvalidConfigError  # type: ignore

from .bridge_impl import FileStorageImpl
from .exceptions import ConfigurationError, GDriveError
from .settings import GDriveStorageSettings

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

    @classmethod
    def login(cls, settings_file: str = "google-oauth-settings.yaml") -> GoogleAuth:
        """login via cli

        Args:
            settings_file (str, optional): Google authentication settings file path. 
            Defaults to "google-oauth-settings.yaml".

        Raises:
            ConfigurationError: raises configuration error in case of missing secrets
        """
        if not hasattr(cls, "_gauth"):
            LOGGER.info("Authenticating to google")
            try:
                cls._gauth = GoogleAuth(settings_file=settings_file)
                cls._gauth.CommandLineAuth()  # type: ignore
            except InvalidConfigError:
                raise ConfigurationError("Cannot find client_secrets.json")
        elif cls._gauth.access_token_expired:  # type: ignore
            raise GDriveError("GoogleDrive authentication token expired")

        return cls._gauth


class GDriveUploadManager():
    """handles gdrive upload management, enqueues files, start/stop workers,...
    """
    _MAX_WORKERS: ClassVar[int] = 3

    def __init__(self, upload_fn: Callable[[str], None], queue_size: int = 100) -> None:
        """ctor

        Args:
            upload_fn (Callable[[str], None]): function to upload file
            queue_size (int, optional): gdrive upload queue size. Defaults to 100.
        """
        self._stop_event = Event()
        self._queue: Queue[str] = Queue(maxsize=queue_size)
        self._upload_fn = upload_fn
        self._executor = ThreadPoolExecutor( max_workers=self._MAX_WORKERS, thread_name_prefix='UploadWorkerThread')
        self._worker_futures = None

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
            LOGGER.warn(f"maxium queue length of {self._MAX_WORKERS} reached. Loosing item {file_path}")

    def start(self) -> None:
        """fire up workers

        Raises:
            GDriveError: if upload workers already running
        """
        if self._worker_futures:
            raise GDriveError("Upload workers already running")

        LOGGER.info(f"Starting up workers")
        # set up dictionary of worker futures
        self._worker_futures = dict(
            enumerate([
                self._executor.submit(self._upload_worker)
                for _ in range(self._MAX_WORKERS
                               )]
                      ))

    def stop(self) -> None:
        """stop workers gracefully

        Args:
            timeout_sec (float, optional): timeout seconds. Defaults to 10.0.

        Raises:
            GDriveError: if daemon failed to stop within timeout
        """
        if not self._worker_futures:
            LOGGER.debug("Trying to stop workers, but none was running before")
            return

        LOGGER.info("Shutting down workers")
        self._stop_event.set()
        LOGGER.debug("Cancel futures")
        for _, worker_future in self._worker_futures.items():
            worker_future.cancel()

        LOGGER.debug("Shutdown executor workers")
        self._executor.shutdown(wait=True)

        self._worker_futures = None
        self._stop_event.clear()

        LOGGER.info("Shutdown successful")

    def _upload_worker(self) -> None:
        LOGGER.info("Init")

        try:
            # wait between 100ms...500ms for eventual stop
            while not self._stop_event.wait(round(uniform(0.1, 0.5), 1)):
                try:
                    file = self._queue.get_nowait()
                except Empty:
                    # queue is empty, continue loop
                    continue

                try:
                    LOGGER.debug(f"Starting upload: {file}")
                    self._upload_fn(file)
                    LOGGER.debug(f"Upload successful: {file}")
                except GDriveError as e:
                    LOGGER.warn(f"Upload failed: {file} with error: {e}")
                finally:
                    # indicate formerly enqueued task is done
                    self._queue.task_done()

        except Exception as e:
            LOGGER.error("Unrecoverable error in upload worker", exc_info=e)

        LOGGER.info("Exit")


class GDriveStorage(FileStorageImpl):
    """ Manages GDrive file upload
    """
    _LOCK: ClassVar[Lock] = Lock()
    _id: ClassVar[int] = 0

    def __init__(self, settings: GDriveStorageSettings):
        self._upload_folder_name = settings.upload_folder_name
        self._upload_man = GDriveUploadManager(self.upload)
        GDriveStorage._id += 1

    def authenticate(self) -> None:
        """authenticate to gdrive via cli
        """
        GDriveStorageAuth.login()

    def start(self) -> None:
        """start the upload daemon thread
        """
        self._upload_man.start()

    def stop(self) -> None:
        """stop the upload daemon thread
        """
        self._upload_man.stop()

    def enqueue_files(self, files: List[str]) -> None:
        """enqueue file paths for upload

        Args:
            files (List[str]): files to enqueue 
        """
        self._upload_man.enqueue_files(files)

    def upload(self, file: str) -> None:
        """upload given file to gdrive

        Args:
            file (str): file to upload 

        Raises:
            GDriveError: on authentication failure
        """

        gdrive = GoogleDrive(GDriveStorageAuth.login())

        # mutex parent folder creation
        with GDriveStorage._LOCK:
            # create the root folder
            root_folder = GDriveStorage._create_file(
                gdrive=gdrive,
                name=self._upload_folder_name,
                mimetype=GDriveMimetype.FOLDER,
                parent_id='root')

            # create directory with the current date
            cur_date = date.today().strftime("%Y%m%d")
            date_folder = GDriveStorage._create_file(
                gdrive=gdrive,
                name=cur_date,
                mimetype=GDriveMimetype.FOLDER,
                parent_id=root_folder['id']  # type: ignore
            )
        # released lock with ctx manager

        # check if file path is a file with os.path.isfile
        file_name = path.basename(file)
        gdrive_file = GDriveStorage._create_file(
            gdrive=gdrive,
            name=file_name,
            mimetype=GDriveMimetype.JPEG,
            parent_id=date_folder['id']  # type: ignore
        )

        LOGGER.info("Uploading file: "
                    f"'{self._upload_folder_name}/{cur_date}/{file_name}'")

        gdrive_file.SetContentFile(file)  # type: ignore
        gdrive_file.Upload()  # type: ignore

        LOGGER.info("Upload file finished: "
                    f"'{self._upload_folder_name}/{cur_date}/{file_name}'")

    @classmethod
    def _create_file(cls, *, gdrive: GoogleDrive, name: str, mimetype: GDriveMimetype,
                     parent_id: Optional[str] = None) -> GoogleDriveFile:
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
        existing_files = cls._search_file(gdrive, name, mimetype, parent_id)
        if existing_files:
            if len(existing_files) > 1:
                raise GDriveError(f"Multiple files ('{name}') found under"
                                  f"given parent {parent_id}")

            file: GoogleDriveFile = existing_files[0]
            LOGGER.debug(f"Found existing file, name: '{name}', id: '{file['id']}', "
                         f"parent: '{parent_id}'")
        else:
            resource = {
                'title': name,
                'mimeType': mimetype.value
            }

            if parent_id:
                resource.update({
                    'parents': [{
                        'id': parent_id
                    }]
                })

            file: GoogleDriveFile = gdrive.CreateFile(resource)  # type: ignore
            file.Upload()  # type: ignore
            LOGGER.debug(f"Created file, name: '{name}', id: '{file['id']}', "
                         f"parent: '{parent_id}'")

        return file

    @classmethod
    def _search_file(cls, gdrive: GoogleDrive, name: str,
                     mimetype: Optional[GDriveMimetype] = None,
                     parent_id: Optional[str] = None) -> Sequence[GoogleDriveFile]:
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

        query = {
            'q': cls._build_query(title=name,
                                  mimetype=mimetype,
                                  parent_id=parent_id)
        }
        return gdrive.ListFile(query).GetList()  # type: ignore

    @classmethod
    def _build_query(cls, *, title: str, mimetype: Optional[GDriveMimetype] = None,
                     trashed: bool = False, parent_id: Optional[str] = None) -> str:
        parent_filter = f"and '{parent_id}' in parents " if parent_id else ""
        mimetype_filter = f"and mimeType='{mimetype.value}' " if mimetype else ""

        return f"title='{title}' " \
            f"{mimetype_filter}" \
            f"{parent_filter}" \
            f"and trashed={str(trashed).lower()}"

    @property
    def id(self) -> int:
        return GDriveStorage._id
