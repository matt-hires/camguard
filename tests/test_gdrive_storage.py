from unittest.case import skip
from camguard.gdrive_storage import GDriveMimetype, GDriveStorage, GDriveStorageAuth, GDriveUploadDaemon
import datetime
import os
from unittest import TestCase
from time import sleep
from unittest.mock import MagicMock, call, create_autospec, patch

from camguard.exceptions import ConfigurationError
from camguard.exceptions import GDriveError
from pydrive.drive import GoogleDrive, GoogleDriveFile
from pydrive.settings import InvalidConfigError


class GDriveStorageTest(TestCase):

    # GDriveStorage has its own imported version of GoogleAuth,
    # therefore it's necessary to patch this one
    @patch("camguard.gdrive_storage.GoogleAuth")
    @patch("camguard.gdrive_storage.GoogleDrive")
    def setUp(self, _, gdrive):
        self.auth: GDriveStorageAuth = GDriveStorageAuth()
        self.sut: GDriveStorage = GDriveStorage(self.auth)
        self.gdrive = gdrive

    @patch("os.path.exists", MagicMock(spec=os.path.exists, return_value=False))
    def test_should_raise_error_when_no_client_secrets(self):
        # arrange
        self.auth._gauth.CommandLineAuth.side_effect = InvalidConfigError("Test")

        # act / assert
        with self.assertRaises(ConfigurationError):
            self.auth.login()

        self.auth._gauth.CommandLineAuth.assert_called()

    def test_should_authenticate(self):
        # arrange

        # act
        self.auth.login()

        # assert
        self.auth._gauth.CommandLineAuth.assert_called()

    def test_should_create_root(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        file = "capture1.jpeg"

        # mock root folder query
        self.sut._search_file = MagicMock(return_value=[])

        create_folder_dict = {
            'title': self.sut.upload_folder_title,
            'mimeType': GDriveMimetype.FOLDER.value,
            'parents': [{'id': 'root'}]
        }

        # act
        self.sut.upload(file)

        # assert
        self.sut._gdrive.CreateFile.assert_has_calls([call(create_folder_dict)],
                                                     any_order=True)

    def test_should_raise_error_when_more_than_one_root_found(self):
        # arrange
        file = "capture1.jpeg"
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        folder = MagicMock(spec=GoogleDriveFile)
        self.sut._search_file = MagicMock(return_value=[folder, folder])

        # act
        with self.assertRaises(GDriveError):
            self.sut.upload(file)

        # assert
        self.sut._gdrive.CreateFile.assert_not_called()

    def test_should_create_date_folder(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        file = "capture1.jpeg"

        # mock root folder query
        root_folder = MagicMock(spec=GoogleDriveFile)
        root_folder.__getitem__ = MagicMock(key="id", return_value="camguard_id")
        self.sut._search_file = MagicMock(side_effect=[
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
        self.sut.upload(file)

        # assert
        self.sut._gdrive.CreateFile.assert_has_calls([call(create_folder_dict)],
                                                     any_order=True)

    def test_should_upload_file(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        file = "capture1.jpeg"
        gdrive_folder = MagicMock(spec=GoogleDriveFile)
        gdrive_folder.__getitem__ = MagicMock(key="id", return_value="folder_id")

        # mock search
        self.sut._search_file = MagicMock(side_effect=[
            [gdrive_folder],  # root folder
            [gdrive_folder],  # date folder
            []  # file
        ])

        # act
        self.sut.upload(file)

        # assert
        create_file_dict = {
            'title': file,
            'mimeType': GDriveMimetype.JPEG.value,
            'parents': [{'id': "folder_id"}]
        }
        self.sut._gdrive.CreateFile.assert_called_with(create_file_dict)
