from pydrive.auth import GoogleAuth
import datetime
import os
from unittest import TestCase
from unittest.mock import MagicMock, call, create_autospec, patch

from camguard.exceptions import ConfigurationError
from camguard.exceptions import GDriveError
from pydrive.drive import GoogleDrive, GoogleDriveFile
from pydrive.settings import InvalidConfigError
from camguard.gdrive_storage import GDriveMimetype, GDriveStorage, GDriveStorageAuth


class GDriveStorageTest(TestCase):

    @patch("os.path.exists", MagicMock(spec=os.path.exists, return_value=False))
    # GDriveStorage has its own imported version of GoogleAuth,
    # therefore it's necessary to patch this one
    @patch("camguard.gdrive_storage.GoogleAuth")
    def test_should_raise_error_when_no_client_secrets(self, gauth):
        # arrange
        gauth.CommandLineAuth.side_effect = InvalidConfigError("Test")
        gauth.return_value=gauth # otherwise constructor call would return wrong mock 
        self.sut: GDriveStorage = GDriveStorage()

        # act / assert
        with self.assertRaises(ConfigurationError):
            self.sut.authenticate()

        gauth.CommandLineAuth.assert_called()

    @patch("camguard.gdrive_storage.GoogleAuth")
    def test_should_authenticate(self, gauth):
        # arrange
        self.sut: GDriveStorage = GDriveStorage()
        gauth.CommandLineAuth = MagicMock()
        gauth.return_value=gauth # otherwise ctor call would return wrong mock 

        # act
        self.sut.authenticate()

        # assert
        gauth.CommandLineAuth.assert_called()

    @patch("camguard.gdrive_storage.GoogleDrive")
    def test_should_create_root(self, gdrive):
        # arrange
        file = "capture1.jpeg"
        gdrive.CreateFile = MagicMock()
        gdrive.return_value = gdrive # otherwise ctor call would return wrong mock

        # mock root folder query
        GDriveStorage._search_file = MagicMock(return_value=[])

        create_folder_dict = {
            'title': GDriveStorage._upload_folder_title,
            'mimeType': GDriveMimetype.FOLDER.value,
            'parents': [{'id': 'root'}]
        }

        # act
        GDriveStorage.upload(file)

        # assert
        gdrive.CreateFile.assert_has_calls([call(create_folder_dict)], any_order=True)

    @patch("camguard.gdrive_storage.GoogleDrive")
    def test_should_raise_error_when_more_than_one_root_found(self, gdrive):
        # arrange
        gdrive.CreateFile = MagicMock()
        gdrive.return_value = gdrive # otherwise ctor call would return wrong mock
        file = "capture1.jpeg"
        folder = MagicMock(spec=GoogleDriveFile)
        GDriveStorage._search_file = MagicMock(return_value=[folder, folder])

        # act
        with self.assertRaises(GDriveError):
            GDriveStorage.upload(file)

        # assert
        gdrive.CreateFile.assert_not_called()

    @patch("camguard.gdrive_storage.GoogleDrive")
    def test_should_create_date_folder(self, gdrive):
        # arrange
        gdrive.CreateFile = MagicMock()
        gdrive.return_value = gdrive # otherwise ctor call would return wrong mock
        file = "capture1.jpeg"

        # mock root folder query
        root_folder = MagicMock(spec=GoogleDriveFile)
        root_folder.__getitem__ = MagicMock(key="id", return_value="camguard_id")
        GDriveStorage._search_file = MagicMock(side_effect=[
            [root_folder],  # root folder
            [],  # date folder
            []  # file
        ])

        date_str = datetime.date.today().strftime("%Y%m%d")
        create_folder_dict = {
            'title': date_str,
            'mimeType': GDriveMimetype.FOLDER.value,
            'parents': [{'id': 'camguard_id'}]
        }

        # act
        GDriveStorage.upload(file)

        # assert
        gdrive.CreateFile.assert_has_calls([call(create_folder_dict)], any_order=True)

    @patch("camguard.gdrive_storage.GoogleDrive")
    def test_should_upload_file(self, gdrive):
        # arrange
        gdrive.CreateFile = MagicMock()
        gdrive.return_value = gdrive # otherwise ctor call would return wrong mock
        file = "capture1.jpeg"
        gdrive_folder = MagicMock(spec=GoogleDriveFile)
        gdrive_folder.__getitem__ = MagicMock(key="id", return_value="folder_id")

        # mock search
        GDriveStorage._search_file = MagicMock(side_effect=[
            [gdrive_folder],  # root folder
            [gdrive_folder],  # date folder
            []  # file
        ])

        # act
        GDriveStorage.upload(file)

        # assert
        create_file_dict = {
            'title': file,
            'mimeType': GDriveMimetype.JPEG.value,
            'parents': [{'id': "folder_id"}]
        }
        gdrive.CreateFile.assert_called_with(create_file_dict)

    def tearDown(self) -> None:
        GDriveStorageAuth._gauth = None
