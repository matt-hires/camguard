import os
from typing import Sequence
from unittest import TestCase
from unittest.mock import MagicMock, create_autospec, patch

from pydrive.files import GoogleDriveFileList

from camguard.exceptions.configuration_error import ConfigurationError
from camguard.gdrive.gdrive_facade import GDriveFacade
from pydrive import drive
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive, GoogleDriveFile
from pydrive.settings import InvalidConfigError


class GDriveFacadeTest(TestCase):

    def setUp(self) -> None:
        self.sut = GDriveFacade()

    @patch("os.path.exists", MagicMock(spec=os.path.exists, return_value=False))
    def test_should_raise_error_when_no_client_secrets(self):
        # arrange
        self.sut._gauth = create_autospec(spec=GoogleAuth)
        self.sut._gauth.CommandLineAuth.side_effect = InvalidConfigError(
            "Test")

        # act / assert
        with self.assertRaises(ConfigurationError):
            self.sut.authenticate()

        self.sut._gauth.CommandLineAuth.assert_called_once()

    @patch.object(GoogleDrive, "__init__", return_value=None)
    def test_should_authenticate(self, gdrive_mock: MagicMock):
        # arrange
        self.sut._gauth = create_autospec(spec=GoogleAuth)

        # act
        self.sut.authenticate()

        # assert
        self.sut._gauth.CommandLineAuth.assert_called_once()
        gdrive_mock.assert_called_once()

    def test_should_create_root(self):
        # arrange
        upload_files = ["capture1.jpeg", "capture2.jpeg"]
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        search_query = {
            'q': f"title='{self.sut.upload_root_path}' "
            "and mimeType='application/vnd.google-apps.folder' "
            "and 'root' in parents "
            "and trashed=false"
        }
        gdrive_file_list = MagicMock(spec=GoogleDriveFileList)
        gdrive_file_list.GetList = MagicMock(return_value=[])
        self.sut._gdrive.ListFile = MagicMock(args=search_query,
                                              return_value=gdrive_file_list)

        create_folder_dict = {
            'title': self.sut.upload_root_path,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        # act
        self.sut.upload(upload_files)

        # assert
        self.sut._gdrive.CreateFile.assert_called_once_with(create_folder_dict)

    def test_should_raise_error_when_search_file_no_filename(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)

        # act / assert
        with self.assertRaises(ValueError):
            self.sut.search_file("")

        self.sut._gdrive.ListFile.assert_not_called()

    def test_should_search_file_with_parent(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        file_name = "upload.jpeg"
        parent_id = "12345"
        search_query = {
            'q': f"title='{file_name}' and '{parent_id}' in parents and trashed=false"
        }

        # act
        self.sut.search_file(file_name, parent_id)

        # assert
        self.sut._gdrive.ListFile.assert_called_once_with(search_query)

    def test_should_search_file(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        file_name = "upload.jpeg"
        search_query = {
            'q': f"title='{file_name}' and trashed=false"
        }

        # act
        self.sut.search_file(file_name)

        # assert
        self.sut._gdrive.ListFile.assert_called_once_with(search_query)

    def test_should_raise_error_when_search_folder_no_foldername(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)

        # act / assert
        with self.assertRaises(ValueError):
            self.sut.search_folder("")

        self.sut._gdrive.ListFile.assert_not_called()

    def test_should_search_folder(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        folder_name = "Camguard"
        search_query = {
            'q': f"title='{folder_name}' "
            "and mimeType='application/vnd.google-apps.folder' "
            "and trashed=false"
        }

        # act
        self.sut.search_folder(folder_name)

        # assert
        self.sut._gdrive.ListFile.assert_called_once_with(search_query)
