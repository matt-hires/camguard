import logging
from datetime import date
from os import path
from typing import Dict, Sequence

from .exceptions import ConfigurationError, GDriveError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import GoogleDriveFile
from pydrive.settings import InvalidConfigError

LOGGER = logging.getLogger(__name__)


class GDriveStorage:
    """ Class for wrapping gdrive access and authentication
    """
    # TODO: Refactor this with QueryObject
    # query string to search a folder
    query_folder_w_title: str = "title='{folder_title}' "\
        "and mimeType='application/vnd.google-apps.folder' "\
        "and trashed=false"
    # query string to search a root folder
    query_folder_w_title_parent: str = "title='{folder_title}' "\
        "and mimeType='application/vnd.google-apps.folder' "\
        "and '{parent_id}' in parents " \
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
            upload_root_path (str, optional): upload folder name, will be
            created in root. Defaults to "camguard". """
        self._gauth: GoogleAuth = GoogleAuth()
        self._gdrive: GoogleDrive = None
        self._shutdown: bool = False
        self.upload_root_path: str = upload_root_path

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
            files (Sequence[str]): filepaths to upload
        """
        found_root_folders: Sequence[GoogleDriveFile] = self.search_folder(
            self.upload_root_path, 'root')
        root_folder: GoogleDriveFile = None
        if not found_root_folders:
            root_folder = self._gdrive.CreateFile({
                'title': self.upload_root_path,
                'mimeType': 'application/vnd.google-apps.folder'
            })
        else:
            if len(found_root_folders) > 1:
                raise GDriveError(f"Multiple root folders '{self.upload_root_path}' found")
            root_folder = found_root_folders[0]
            LOGGER.debug(f"Found root folder '{self.upload_root_path}'"
                         f"with id '{root_folder['id']}'")

        # create directory with the current date
        cur_date: str = date.today().strftime("%Y%m%d")
        found_date_folders: Sequence[GoogleDriveFile] = self.search_folder(cur_date)
        date_folder: GoogleDriveFile = None

        if not found_date_folders:
            date_folder = self._gdrive.CreateFile({
                'title': cur_date,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [{'id': root_folder['id']}]
            })
            LOGGER.debug(f"Creating date folder '{cur_date}' ...")
            date_folder.Upload()
        else:
            if len(found_date_folders) > 1:
                raise GDriveError(
                    f"Multiple date folders '{cur_date}' found")
            date_folder = found_date_folders[0]
            LOGGER.debug(f"Found date folder '{cur_date}' with id '{date_folder['id']}'")

        for file in files:
            if self._shutdown:
                LOGGER.debug("Upload interrupted by shutdown")
                break

            # check if file path is a file with os.path.isfile
            file_name = path.basename(file)

            gdrive_file: GoogleDriveFile = None
            found_gdrive_files: Sequence[GoogleDriveFile] = None
            if found_date_folders:
                found_gdrive_files = self.search_file(file_name, date_folder['id'])

                if len(found_gdrive_files) > 1:
                    raise GDriveError(
                        f"Multiple gdrive files '{file_name}' found")

            if found_gdrive_files:
                gdrive_file = found_gdrive_files[0]
                LOGGER.debug(f"Found file '{file_name}' with id '{gdrive_file['id']}'")
            else:
                LOGGER.debug(f"Creating file '{file_name}' in folder: '{date_folder['id']}'")
                gdrive_file = self._gdrive.CreateFile({
                    'title': file_name,
                    'mimeType': 'image/jpeg',
                    'parents': [{'id': date_folder['id']}]
                })

            LOGGER.info(f"Uploading file '{file_name}' "
                        f"to '{self.upload_root_path}/{cur_date}' ...")

            gdrive_file.SetContentFile(file)
            gdrive_file.Upload()

        LOGGER.info("Finished gdrive upload")

    def search_file(self, file_name: str,
                    parent_id: str = None) -> Sequence[GoogleDriveFile]:
        """search for a file on google drive with certain parameters

        Args:
            file_name (str): the human readable name of the file
            parent_id (str, optional): parent/folder id where the file is 
            located in. Defaults to None.

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
                'q': GDriveStorage.query_file_w_title_parent.format(
                    file_title=file_name, parent_id=parent_id)
            }
        else:
            query = {
                'q': GDriveStorage.query_file_w_title.format(
                    file_title=file_name)
            }

        return self._gdrive.ListFile(query).GetList()

    def search_folder(self, folder_name: str,
                      parent_id: str = None) -> Sequence[GoogleDriveFile]:
        """search for a folder on google drive with certain parameters

        Args:
            folder_name (str): the human readable name of the folder
            parent_id (str, optional): A parent id under which the folder is 
            located or 'root'. Defaults to None.

        Raises:
            ValueError: if folder_name is not set 

        Returns:
             Sequence[GoogleDriveFile]: list of found google drive folders
        """

        if not folder_name:
            raise ValueError("folder_name not set")

        query: Dict = None
        if parent_id:
            query = {
                'q': GDriveStorage.query_folder_w_title_parent.format(
                    parent_id=parent_id, folder_title=folder_name)
            }
        else:
            query = {
                'q': GDriveStorage.query_folder_w_title.format(
                    folder_title=folder_name)
            }

        return self._gdrive.ListFile(query).GetList()

    def shutdown(self):
        """shutdown grive upload
        """
        LOGGER.debug(f"Shutting down")
        self._shutdown = True
