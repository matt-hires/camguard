from unittest.case import skip
from camguard.gdrive_facade import GDriveFacade
import datetime
import os
from unittest import TestCase
from unittest.mock import MagicMock, call, create_autospec, patch

from camguard.exceptions import ConfigurationError
from camguard.exceptions import GDriveError
from pydrive.drive import GoogleDrive, GoogleDriveFile
from pydrive.settings import InvalidConfigError


class GDriveFacadeTest(TestCase):

    # GDriveFacade has its own imported version of GoogleAuth, 
    # therefore it's necessary to patch this one
    @patch("camguard.gdrive_facade.GoogleAuth")
    @patch("camguard.gdrive_facade.GoogleDrive")
    def setUp(self, _, gdrive):
        self.sut = GDriveFacade()
        self.gdrive = gdrive

    @patch("os.path.exists", MagicMock(spec=os.path.exists, return_value=False))
    def test_should_raise_error_when_no_client_secrets(self):
        # arrange
        self.sut._gauth.CommandLineAuth.side_effect = InvalidConfigError("Test")

        # act / assert
        with self.assertRaises(ConfigurationError):
            self.sut.authenticate()

        self.sut._gauth.CommandLineAuth.assert_called()

    def test_should_authenticate(self):
        # arrange

        # act
        self.sut.authenticate()

        # assert
        self.sut._gauth.CommandLineAuth.assert_called()
        self.assertTrue(call() in self.gdrive.mock_calls)

    def test_should_create_root(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)

        upload_files = ["capture1.jpeg", "capture2.jpeg"]

        # mock root folder query
        self.sut.search_folder = MagicMock(return_value=[])

        create_folder_dict = {
            'title': self.sut.upload_root_path,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        # act
        self.sut.upload(upload_files)

        # assert
        self.sut._gdrive.CreateFile.assert_any_call(create_folder_dict)

    def test_should_raise_error_when_more_than_one_root_found(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        self.sut.search_folder = MagicMock(return_value=["Root1", "Root2"])

        # act
        with self.assertRaises(GDriveError):
            self.sut.upload(["capture1.jpeg", "capture2.jpeg"])

        # assert
        self.sut._gdrive.CreateFile.assert_not_called()

    def test_should_create_date_folder(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        upload_files = ["capture1.jpeg", "capture2.jpeg"]

        # mock root folder query
        gdrive_root_folder = MagicMock(spec=GoogleDriveFile)
        gdrive_root_folder.__getitem__ = MagicMock(key="id", return_value="test")
        self.sut.search_folder = MagicMock(side_effect=[
            [gdrive_root_folder],  # root folder
            []  # date folder
        ])
        date_str = datetime.date.today().strftime("%Y%m%d")
        create_folder_dict = {
            'title': date_str,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [{'id': 'test'}]
        }

        # act
        self.sut.upload(upload_files)

        # assert
        self.sut._gdrive.CreateFile.assert_any_call(create_folder_dict)

    def test_should_upload_files(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        upload_files = ["capture1.jpeg", "capture2.jpeg"]
        gdrive_folder = MagicMock(spec=GoogleDriveFile)
        gdrive_folder.__getitem__ = MagicMock(key="id", return_value="test")

        # mock root/date folder query
        self.sut.search_folder = MagicMock(side_effect=[
            [gdrive_folder],  # root folder
            [gdrive_folder],  # date folder
        ])
        # mock files
        self.sut.search_file = MagicMock(side_effect=[
            [],  # capture1.jpeg
            []  # capture2.jpeg
        ])

        # act
        self.sut.upload(upload_files)

        # assert
        for file in upload_files:
            create_file_dict = {
                'title': file,
                'mimeType': 'image/jpeg',
                'parents': [{'id': "test"}]
            }
            self.sut._gdrive.CreateFile.assert_any_call(create_file_dict)

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
            'q': f"title='{file_name}' "
                 f"and '{parent_id}' in parents and trashed=false"
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

    def test_should_shutdown(self):
        # arrange
        self.sut._gdrive = create_autospec(spec=GoogleDrive)
        upload_files = ["capture1.jpeg", "capture2.jpeg"]
        gdrive_folder = MagicMock(spec=GoogleDriveFile)
        gdrive_folder.__getitem__ = MagicMock(key="id", return_value="test")

        # mock root/date folder query
        self.sut.search_folder = MagicMock(side_effect=[
            [gdrive_folder],  # root folder
            [gdrive_folder],  # date folder
        ])
        # mock files
        self.sut.search_file = MagicMock(side_effect=[
            [],  # capture1.jpeg
            []  # capture2.jpeg
        ])

        # act
        self.sut.shutdown()
        self.sut.upload(upload_files)

        # assert
        for file in upload_files:
            self.sut._gdrive.CreateFile.assert_not_called()

