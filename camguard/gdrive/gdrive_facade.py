import logging
from typing import Dict, Sequence

from pydrive.files import GoogleDriveFile

from camguard.exceptions.configuration_error import ConfigurationError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.settings import InvalidConfigError

LOGGER = logging.getLogger(__name__)


class GDriveFacade:
    """ Class for wrapping gdrive access and authentication
    """
    # TODO: Refactor this with QueryObject
    # query string to search a folder
    query_folder_w_title: str = "title='{folder_title}' "\
        "and mimeType='application/vnd.google-apps.folder' "\
        "and trashed=false"
    # query string to search a root folder
    query_folder_w_title_root: str = "title='{folder_title}' "\
        "and mimeType='application/vnd.google-apps.folder' "\
        "and 'root' in parents " \
        "and trashed=false"
    # query string to search a file with title
    query_file_w_title: str = "title='{file_title}' "\
        "and trashed=false"
    # query string to get a file with title and parent
    query_file_w_title_parent: str = "title='{file_title}' "\
        "and '{parent_id}' in parents "\
        "and trashed=false"

    def __init__(self, upload_root_path: str = "Camguard"):
        """ctor

        Args:
            upload_root_path (str, optional): upload folder name, will be created in root. Defaults to "camguard".
        """
        self._gauth: GoogleAuth = GoogleAuth()
        self._gdrive: GoogleDrive = None
        self._upload_root_path: str = upload_root_path

    @property
    def upload_root_path(self) -> str:
        return self._upload_root_path

    def authenticate(self):
        """ Authenticate to google drive using oauth
        """

        try:
            self._gauth.CommandLineAuth()
            self._gdrive = GoogleDrive(self._gauth)
        except InvalidConfigError:
            raise ConfigurationError("Cannot find client_secrets.json")

    def upload(self, files: Sequence[str]):
        """upload files to gdrive (authentication needed)

        Args:
            files (Sequence[str]): files to upload
        """
        found_folders: Sequence[GoogleDriveFile] = self.search_folder(self._upload_root_path,
                                                                      is_root=True)

        if not found_folders:
            self._gdrive.CreateFile({
                'title': self._upload_root_path,
                'mimeType': 'application/vnd.google-apps.folder'
            })

        # TODO: upload files

    def search_file(self, file_name: str, parent_id: str = None) -> Sequence[GoogleDriveFile]:
        """search for a file on google drive with certain parameters

        Args:
            file_name (str): the human readable name of the file
            parent_id (str, optional): parent/folder id where the file is located in. Defaults to None.

        Raises:
            ValueError: on empty file name

        Returns:
            Sequence[GoogleDriveFile]: list of found google drive files
        """
        if not file_name:
            raise ValueError("file_name not set")

        query: Dict = None
        if parent_id:
            query = {
                'q': GDriveFacade.query_file_w_title_parent.format(file_title=file_name,
                                                                   parent_id=parent_id)
            }
        else:
            query = {
                'q': GDriveFacade.query_file_w_title.format(file_title=file_name)
            }

        return self._gdrive.ListFile(query).getList()

    def search_folder(self, folder_name: str, is_root: bool = False) -> Sequence[GoogleDriveFile]:
        """search for a folder on google drive with certain parameters

        Args:
            folder_name (str): the human readable name of the folder

        Returns:
            Sequence[GoogleDriveFile]: list of found google drive folders
        """
        if not folder_name:
            raise ValueError("folder_name not set")

        query: Dict = None
        if is_root:
            query = {
                'q': GDriveFacade.query_folder_w_title_root.format(folder_title=folder_name)
            }
        else:
            query = {
                'q': GDriveFacade.query_folder_w_title.format(folder_title=folder_name)
            }

        return self._gdrive.ListFile(query).GetList()
