import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from enum import Enum
from os import path
from queue import Empty, Full, Queue
from random import uniform
from threading import Event, Thread
from typing import Dict, List, Sequence

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
from pydrive.settings import InvalidConfigError

from .exceptions import ConfigurationError, GDriveError

LOGGER = logging.getLogger(__name__)


class GDriveMimetype(Enum):
    """google drive mimetype enumeration
    see https://developers.google.com/drive/api/v3/ref-export-formats for full listing
    """
    FOLDER = "application/vnd.google-apps.folder"
    JPEG = "image/jpeg"


class GDriveStorage:
    """ Class for wrapping gdrive access and authentication
    """

    def __init__(self, upload_folder_title: str = "Camguard"):
        """ctor

        Args:
            upload_folder_title (str, optional): upload folder name, will be
            created in root. Defaults to "camguard". """
        LOGGER.debug(f"Configuring gdrive storage with params: "
                     f"upload_folder_title: {upload_folder_title}")
        self._gauth: GoogleAuth = GoogleAuth(settings_file="google-oauth-settings.yaml")
        self._gdrive: GoogleDrive = None
        self._upload_daemon: GDriveUploadDaemon = GDriveUploadDaemon.getInstance(self)
        self.upload_folder_title: str = upload_folder_title

    def setup(self):
        """setup storage: authenticate and startup upload daemon
        """
        self._authenticate()
        self._upload_daemon.start()

    def shutdown(self):
        """shutdown storage by stopping upload daemon
        """
        self._upload_daemon.stop()

    def enqueue_files(self, files: List[str]):
        """enqueue more files at once for parallel upload 

        Args:
            files (List[str]): list of files to upload 
        """
        for file in files:
            self._upload_daemon.enqueue_file(file)

    def upload(self, file: str) -> None:
        """upload files to gdrive (authentication needed)

        Args:
            files (Sequence[str]): filepaths to upload
        """

        # create the root folder
        root_folder: GoogleDriveFile = self._create_file(
            name=self.upload_folder_title,
            mimetype=GDriveMimetype.FOLDER,
            parent_id='root')

        # create directory with the current date
        cur_date: str = date.today().strftime("%Y%m%d")
        date_folder: GoogleDriveFile = self._create_file(
            name=cur_date,
            mimetype=GDriveMimetype.FOLDER,
            parent_id=root_folder['id']
        )

        # check if file path is a file with os.path.isfile
        file_name = path.basename(file)
        gdrive_file: GoogleDriveFile = self._create_file(
            name=file_name,
            mimetype=GDriveMimetype.JPEG,
            parent_id=date_folder['id']
        )

        LOGGER.info("Uploading file: "
                    f"'{self.upload_folder_title}/{cur_date}/{file_name}' ...")

        gdrive_file.SetContentFile(file)
        gdrive_file.Upload()

        LOGGER.info("Upload file finished: "
                    f"'{self.upload_folder_title}/{cur_date}/{file_name}'")

    def _create_file(self, *, name: str, mimetype: GDriveMimetype,
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
        existing: Sequence[GoogleDriveFile] = self._search_file(name=name,
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

            file = self._gdrive.CreateFile(resource)
            file.Upload()
            LOGGER.debug(f"Created file, name: '{name}', id: '{file['id']}', "
                         f"parent: '{parent_id}'")

        return file

    def _authenticate(self):
        """ Authenticate to google drive using oauth
        """
        LOGGER.info("Authenticating to google")

        try:
            self._gauth.CommandLineAuth()
            self._gdrive = GoogleDrive(self._gauth)
        except InvalidConfigError:
            raise ConfigurationError("Cannot find client_secrets.json")

    def _search_file(self, *, name: str, mimetype: GDriveMimetype = None,
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
            'q': GDriveStorage._build_query(title=name,
                                            mimetype=mimetype,
                                            parent_id=parent_id)
        }
        return self._gdrive.ListFile(query).GetList()

    @staticmethod
    def _build_query(*, title: str, mimetype: GDriveMimetype = None,
                     trashed: bool = False, parent_id: str = None) -> str:
        parent_filter = f"and '{parent_id}' in parents " if parent_id else ""
        mimetype_filter = f"and mimeType='{mimetype.value}' " if mimetype else ""

        return f"title='{title}' " \
            f"{mimetype_filter}" \
            f"{parent_filter}" \
            f"and trashed={str(trashed).lower()}"


class GDriveUploadDaemon(Thread):
    _INSTANCE = None
    _QUEUE_SIZE: int = 100
    _MAX_WORKERS: int = 3
    _WORKER_NAME = "worker-{name}"

    def __init__(self, storage: GDriveStorage) -> None:
        super().__init__(daemon=True)
        self._stop_event = Event()
        self._queue: Queue[str] = Queue(maxsize=GDriveUploadDaemon._QUEUE_SIZE)
        self._storage: GDriveStorage = storage

    @staticmethod
    def getInstance(storage: GDriveStorage):
        if not GDriveUploadDaemon._INSTANCE:
            GDriveUploadDaemon._INSTANCE = GDriveUploadDaemon(storage)
        return GDriveUploadDaemon._INSTANCE

    def enqueue_file(self, file_path: str) -> None:
        LOGGER.debug(f"{GDriveUploadDaemon.__name__} Enqueuing file: {file_path}")
        try:
            self._queue.put_nowait(file_path)
        except Full:
            LOGGER.warn(f"{GDriveUploadDaemon.__name__} maxium queue length of "
            f"{self._MAX_WORKERS} reached. Loosing item {file_path}")
            # TODO: handle full queue and exceptions
            pass

    def run(self) -> None:
        self._stop_event.clear()
        LOGGER.info(f"{GDriveUploadDaemon.__name__} starting up")
        # ThreadPoolExecutor ContextManager blocks till every worker is done
        with ThreadPoolExecutor(max_workers=self._MAX_WORKERS,
                                thread_name_prefix='gdrive_worker') as executor:
            for i in range(self._MAX_WORKERS):
                executor.submit(self._upload_worker, self._WORKER_NAME.format(name=i))

    def stop(self, timeout_sec=10) -> None:
        if not self.is_alive():
            LOGGER.debug(f"{GDriveUploadDaemon.__name__} has already been stopped")
            return

        LOGGER.info(f"{GDriveUploadDaemon.__name__} shutting down gracefully")
        self._stop_event.set()
        self.join(timeout_sec)

    def _upload_worker(self, name):
        # wait between 100ms...500ms for eventual stop
        while not self._stop_event.wait(round(uniform(0.1, 0.5), 1)):
            try:
                file = self._queue.get_nowait()
            except Empty:
                pass
            else:
                try:
                    LOGGER.debug("f{name} starting upload: {file}")
                    self._storage.upload(file)
                    LOGGER.debug("f{name} upload successful: {file}")
                except Exception as e:
                    LOGGER.error(f"{name} upload failed: {file} error: {e}")

        LOGGER.debug(f"{name} finished")
