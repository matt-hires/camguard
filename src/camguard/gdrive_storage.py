import logging
from datetime import date
from enum import Enum
from os import path
from typing import Dict, Sequence

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
        self.upload_folder_title: str = upload_folder_title

    def authenticate(self):
        """ Authenticate to google drive using oauth
        """
        LOGGER.info("Authenticating to google")

        try:
            self._gauth.CommandLineAuth()
            self._gdrive = GoogleDrive(self._gauth)
        except InvalidConfigError:
            raise ConfigurationError("Cannot find client_secrets.json")

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
