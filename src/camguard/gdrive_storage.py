import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from enum import Enum
from os import path
from queue import Empty, Full, Queue
from random import uniform
from threading import Event, Lock
from typing import Any, Callable, ClassVar, Dict, List, Optional, Sequence

from google.oauth2.credentials import Credentials, exceptions  # type: ignore
from google.auth.transport.requests import Request  # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
from googleapiclient.discovery import build  # type: ignore
from googleapiclient.http import MediaFileUpload  # type: ignore

from camguard.file_storage_settings import GDriveStorageSettings

from camguard.bridge_impl import FileStorageImpl
from camguard.exceptions import GDriveError

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
    # If modifying these scopes, delete the file token.json.
    _SCOPES: ClassVar[List[str]] = ['https://www.googleapis.com/auth/drive.file']

    @classmethod
    def authenticate(cls, settings: GDriveStorageSettings) -> Credentials:
        """
        Authenticate to gdrive with user credentials in credentials.json

        Args:
            settings_file (str, optional): Google authentication settings file path. 
            Defaults to "google-oauth-settings.yaml".

        Raises:
            ConfigurationError: raises configuration error in case of missing secrets
        """
        creds = None
        token_path: str = path.join(path.expandvars(path.expanduser(settings.oauth_token_path)), 'token.json')

        LOGGER.debug(f"Getting login token from: {token_path}")

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, cls._SCOPES)  # type: ignore

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:  # type: ignore
                LOGGER.debug("Refreshing expired credentials")
                try:
                    creds.refresh(Request())  # type: ignore
                except exceptions.RefreshError as oauth_ex:
                    raise GDriveError(f"Cannot refresh access token: {oauth_ex}")
            else:
                credentials_path: str = path.join(path.expandvars(path.expanduser(settings.oauth_credentials_path)),
                                                  'credentials.json')
                LOGGER.debug(f"Authenticating with credentials from: {credentials_path}")

                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, cls._SCOPES)  # type: ignore
                creds = flow.run_local_server()  # type: ignore
            # Save the credentials for the next run
            with open(token_path, 'w') as token:
                token.write(creds.to_json())  # type: ignore

        return creds


class GDriveUploadManager():
    """handles gdrive upload management, enqueues files, start/stop workers,...
    """
    __MAX_WORKERS: ClassVar[int] = 3

    def __init__(self, upload_fn: Callable[[str], None], queue_size: int = 100) -> None:
        """ctor

        Args:
            upload_fn (Callable[[str], None]): function to upload file
            queue_size (int, optional): gdrive upload queue size. Defaults to 100.
        """
        self.__stop_event = Event()
        self.__queue: Queue[str] = Queue(maxsize=queue_size)
        self.__upload_fn = upload_fn
        self.__executor = ThreadPoolExecutor(max_workers=self.__MAX_WORKERS, thread_name_prefix='UploadWorkerThread')
        self.__worker_futures = None

    def enqueue_files(self, files: List[str]) -> None:
        """enqueue files for upload.

        Args:
            files (List[str]): path of the files to enqueue 
        """
        for file in files:
            self.__enqueue_file(file)

    def __enqueue_file(self, file_path: str) -> None:
        LOGGER.debug(f"Enqueuing file: {file_path}")
        try:
            self.__queue.put_nowait(file_path)
        except Full:
            LOGGER.warning(f"Maximum queue length of {self.__queue.maxsize} reached. Loosing item {file_path}")

    def start(self) -> None:
        """fire up workers

        Raises:
            GDriveError: if upload workers already running
        """
        if self.__worker_futures:
            raise GDriveError("Upload workers already running")

        LOGGER.info("Starting up workers")
        # set up dictionary of worker futures
        self.__worker_futures = dict(
            enumerate(self.__executor.submit(self.__upload_worker) for _ in range(self.__MAX_WORKERS))
        )

    def stop(self) -> None:
        """stop workers gracefully

        Args:
            timeout_sec (float, optional): timeout seconds. Defaults to 10.0.

        Raises:
            GDriveError: if daemon failed to stop within timeout
        """
        if not self.__worker_futures:
            LOGGER.debug("Trying to stop workers, but none was running before")
            return

        LOGGER.info("Shutting down workers")
        self.__stop_event.set()
        LOGGER.debug("Cancel futures")
        for _, worker_future in self.__worker_futures.items():
            worker_future.cancel()

        LOGGER.debug("Shutdown executor workers")
        self.__executor.shutdown(wait=True)

        self.__worker_futures = None
        self.__stop_event.clear()

        LOGGER.info("Shutdown successful")

    def __upload_worker(self) -> None:
        LOGGER.info("Init")

        # wait between 100ms...500ms for eventual stop
        while not self.__stop_event.wait(round(uniform(0.1, 0.5), 1)):
            try:
                file = self.__queue.get_nowait()
            except Empty:
                # queue is empty, continue loop
                continue

            try:
                LOGGER.debug(f"Starting upload: {file}")
                self.__upload_fn(file)
                LOGGER.debug(f"Upload successful: {file}")
            # skipcq: PYL-W0703
            except Exception as e:
                # errors do not stop the thread,
                # so that the upload component can recover from google drive errors
                LOGGER.warning(f"Upload failed: {file}", exc_info=e)
            finally:
                # indicate formerly enqueued task is done
                # therefore also a unsuccessful upload, in case of an Error, won't lead to a retry
                # the queue should be ready for new work and not be flooded with old upload retries
                self.__queue.task_done()

        LOGGER.info("Exit")


class GDriveStorage(FileStorageImpl):
    """ Manages GDrive file upload
    """
    __LOCK: ClassVar[Lock] = Lock()
    __id: ClassVar[int] = 0

    def __init__(self, settings: GDriveStorageSettings):
        self.__upload_folder_name = settings.upload_folder_name
        self.__upload_man = GDriveUploadManager(self.upload)
        self.__settings = settings
        GDriveStorage.__id += 1

    @property
    def id(self) -> int:
        return GDriveStorage.__id

    def authenticate(self) -> None:
        """authenticate to gdrive via cli
        """
        GDriveStorageAuth.authenticate(self.__settings)

    def start(self) -> None:
        """start the upload daemon thread
        """
        self.__upload_man.start()

    def stop(self) -> None:
        """stop the upload daemon thread
        """
        self.__upload_man.stop()

    def enqueue_files(self, files: List[str]) -> None:
        """enqueue file paths for upload

        Args:
            files (List[str]): files to enqueue 
        """
        self.__upload_man.enqueue_files(files)

    def upload(self, file: str) -> None:
        """upload given file to gdrive

        Args:
            file (str): file to upload 

        Raises:
            GDriveError: on authentication failure
        """

        creds = GDriveStorageAuth.authenticate(self.__settings)

        # mutex parent folder creation
        with GDriveStorage.__LOCK:
            # create the root folder
            root_folder = GDriveStorage.__create_folder(
                creds=creds,
                name=self.__upload_folder_name,
                parent_id='root')

            # create directory with the current date
            cur_date = date.today().strftime("%Y%m%d")
            date_folder = GDriveStorage.__create_folder(
                creds=creds,
                name=cur_date,
                parent_id=root_folder['id'])

        # released lock with ctx manager

        # check if file path is a file with os.path.isfile
        file_name = path.basename(file)
        LOGGER.info(f"Uploading file: {file}")

        GDriveStorage.__create_file(
            creds=creds,
            file_name=file_name,
            file_path=file,
            mimetype=GDriveMimetype.JPEG,
            parent_id=date_folder['id'])

        LOGGER.info("Upload file finished: "
                    f"'{self.__upload_folder_name}/{cur_date}/{file_name}'")

    @classmethod
    def __create_folder(cls, *, creds: Credentials, name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        existing = cls.__search_file(creds, name, GDriveMimetype.FOLDER, parent_id)

        if existing:
            if len(existing) > 1:
                raise GDriveError(f"Multiple folders ('{name}') found under"
                                  f"given parent {parent_id}")

            for existing_folder in existing:
                LOGGER.debug(f"Found existing folder, name: '{existing_folder['name']}' "
                             f"id: '{existing_folder['id']}', "
                             f"parents: '{existing_folder['parents']}'")
            folder = existing[0]
        else:
            file_metadata: Dict[str, Any] = {
                'name': name,
                'mimeType': GDriveMimetype.FOLDER.value
            }

            if parent_id:
                file_metadata.update({'parents': [parent_id]})

            with build(serviceName='drive', version='v3', credentials=creds) as gdrive_service:  # type: ignore
                response = gdrive_service.files().create(body=file_metadata,  # type: ignore
                                                         fields='id, name, parents').execute()
                folder: Dict[str, Any] = {'id': response['id'],
                                          'name': response['name'],
                                          'parents': response['parents']}
                LOGGER.debug("Created folder, "
                             f"id: '{folder['id']}' name: '{folder['name']}' parents: '{folder['parents']}'")

        return folder

    @classmethod
    def __create_file(cls, *, creds: Credentials, file_name: str, file_path: str, mimetype: GDriveMimetype,
                      parent_id: Optional[str] = None) -> Dict[str, Any]:
        """create file or folder on gdrive storage if it's not already existing

        Args:
            file_name (str): name of the file/folder to create
            mimetype (GDriveMimetype): mimetype for file or folder 
            parent_id (str, optional): parent where the file or folder should be 
            located in. Defaults to None.

        Raises:
            GDriveError: if multiple folders where found with the given name under 
            the given parent id

        Returns:
            Dict[str, Any]: properties of the created file 
        """
        file: Dict[str, Any]
        existing_files = cls.__search_file(creds, file_name, mimetype, parent_id)
        if existing_files:
            if len(existing_files) > 1:
                raise GDriveError(f"Multiple files ('{file_name}') found under"
                                  f"given parent {parent_id}")

            file = existing_files[0]
            LOGGER.debug(f"Found existing file, name: '{file['name']}', id: '{file['id']}', "
                         f"parents: '{file['parents']}'")
        else:
            file_metadata: Dict[str, Any] = {
                'name': file_name
            }

            if parent_id:
                file_metadata.update({'parents': [parent_id]})

            media = MediaFileUpload(filename=file_path, mimetype=mimetype.value)
            with build(serviceName='drive', version='v3', credentials=creds) as gdrive_service:  # type: ignore
                response = gdrive_service.files().create(body=file_metadata,  # type: ignore
                                                         media_body=media,
                                                         fields='id, name, parents').execute()
                file = {'id': response['id'],
                        'name': response['name'],
                        'parents': response['parents']}
                LOGGER.debug(f"Created file, id: '{file['id']}' name: '{file['name']}' parents: '{file['parents']}'")

        return file

    @classmethod
    def __search_file(cls, creds: Credentials, file_name: str,
                      mimetype: Optional[GDriveMimetype] = None,
                      parent_id: Optional[str] = None) -> Sequence[Dict[str, Any]]:
        """search for a file/folder on google drive with certain parameters

        Args:
            file_name (str): the human readable name of the file or folder
            mimetype (GDriveMimetype, optional): mimetype of the file to search.
            Defaults to None
            parent_id (str, optional): parent/folder id where the file is 
            located in. Defaults to None.

        Raises:
            ValueError: on empty file name

        Returns:
            Sequence[Dict[str, Any]]: list of properties of the found files 
        """
        if not file_name:
            raise ValueError("File name not set")

        query = cls.__build_query(name=file_name, mimetype=mimetype, parent_id=parent_id)
        found_files: List[Dict[str, Any]] = []
        with build(serviceName='drive', version='v3', credentials=creds) as gdrive_service:  # type: ignore
            page_token = None
            while True:
                response = gdrive_service.files().list(q=query,  # type: ignore
                                                       spaces='drive',
                                                       fields='nextPageToken, files(id, name, parents)',
                                                       pageToken=page_token).execute()

                for file in response.get('files', []):  # type: ignore
                    found_files.append({
                        'id': file.get('id'),  # type: ignore
                        'name': file.get('name'),  # type: ignore
                        'parents': file.get('parents')  # type: ignore
                    })

                page_token = response.get('nextPageToken', None)  # type: ignore
                if page_token is None:
                    break

        return found_files

    @classmethod
    def __build_query(cls, *, name: str, mimetype: Optional[GDriveMimetype] = None,
                      trashed: bool = False, parent_id: Optional[str] = None) -> str:
        parent_filter = f"and '{parent_id}' in parents " if parent_id else ""
        mimetype_filter = f"and mimeType='{mimetype.value}' " if mimetype else ""

        return f"name='{name}' " \
            f"{mimetype_filter}" \
            f"{parent_filter}" \
            f"and trashed={str(trashed).lower()}"
