import datetime
from time import sleep
from unittest import TestCase
from unittest.mock import MagicMock, call, create_autospec, patch

from pydrive.auth import GoogleAuth # type: ignore
from pydrive.drive import GoogleDrive, GoogleDriveFile # type: ignore
from pydrive.settings import InvalidConfigError # type: ignore

from camguard.exceptions import ConfigurationError, GDriveError
from camguard.gdrive_storage import (GDriveMimetype, GDriveStorage,
                                     GDriveStorageAuth)


class GDriveStorageAuthTest(TestCase):
    def test_should_raise_error_when_no_client_secrets(self):
        # arrange
        gauth_mock = create_autospec(spec=GoogleAuth, spec_set=True)
        gauth_mock.CommandLineAuth.side_effect = InvalidConfigError("Test")

        # act / assert
        with patch("camguard.gdrive_storage.GoogleAuth", return_value=gauth_mock),\
                self.assertRaises(ConfigurationError):
            GDriveStorageAuth.login()

        gauth_mock.CommandLineAuth.assert_called()

    def test_should_authenticate(self):
        # arrange
        gauth_mock = create_autospec(spec=GoogleAuth, spec_set=True)

        # act
        with patch("camguard.gdrive_storage.GoogleAuth", return_value=gauth_mock):
            GDriveStorageAuth.login()

        # assert
        gauth_mock.CommandLineAuth.assert_called()

    def tearDown(self) -> None:
        delattr(GDriveStorageAuth, "_gauth")


class GDriveStorageTest(TestCase):

    @patch("camguard.gdrive_storage.GDriveStorage._search_file",
           MagicMock(return_value=[]))
    @patch("camguard.gdrive_storage.GDriveStorageAuth.login", MagicMock())
    def test_should_create_root(self):
        # arrange
        gdrive_mock = create_autospec(spec=GoogleDrive, spec_set=True)
        # mock root folder query
        create_folder_dict = {
            'title': GDriveStorage._upload_folder_title, # type: ignore
            'mimeType': GDriveMimetype.FOLDER.value,
            'parents': [{'id': 'root'}]
        }
        file = "capture1.jpeg"

        # act
        with patch("camguard.gdrive_storage.GoogleDrive", return_value=gdrive_mock):
            GDriveStorage.upload(file)

        # assert
        gdrive_mock.CreateFile.assert_has_calls([call(create_folder_dict)], any_order=True)

    @patch("camguard.gdrive_storage.GDriveStorage._search_file",
           MagicMock(return_value=[MagicMock(), MagicMock()]))
    @patch("camguard.gdrive_storage.GDriveStorageAuth.login", MagicMock())
    def test_should_raise_error_when_more_than_one_root_found(self):
        # arrange
        gdrive_mock = create_autospec(spec=GoogleDrive, spec_set=True)
        file = "capture1.jpeg"

        # act
        with patch("camguard.gdrive_storage.GoogleDrive", return_value=gdrive_mock),\
                self.assertRaises(GDriveError):
            GDriveStorage.upload(file)

        # assert
        gdrive_mock.CreateFile.assert_not_called()

    @patch("camguard.gdrive_storage.GDriveStorageAuth.login", MagicMock())
    def test_should_create_date_folder(self):
        # arrange
        gdrive_mock = create_autospec(spec=GoogleDrive, spec_set=True)
        file = "capture1.jpeg"
        # mock root folder query
        root_folder = MagicMock(spec=GoogleDriveFile)
        root_folder.__getitem__ = MagicMock(key="id", return_value="camguard_id")
        search_file_mock = MagicMock(side_effect=[
            [root_folder],  # root folder
            [],  # date folder
            []  # file
        ])

        # act
        with patch("camguard.gdrive_storage.GoogleDrive",
                   MagicMock(return_value=gdrive_mock)),\
                patch("camguard.gdrive_storage.GDriveStorage._search_file",
                      search_file_mock):
            GDriveStorage.upload(file)

        # assert
        date_str = datetime.date.today().strftime("%Y%m%d")
        create_folder_dict = {
            'title': date_str,
            'mimeType': GDriveMimetype.FOLDER.value,
            'parents': [{'id': 'camguard_id'}]
        }
        gdrive_mock.CreateFile.assert_has_calls([call(create_folder_dict)], any_order=True)

    @patch("camguard.gdrive_storage.GDriveStorageAuth.login", MagicMock())
    def test_should_upload_file(self):
        # arrange
        gdrive_mock = create_autospec(spec=GoogleDrive, spec_set=True)
        file = "capture1.jpeg"
        folder_mock = MagicMock(spec=GoogleDriveFile)
        folder_mock.__getitem__ = MagicMock(key="id", return_value="folder_id")
        # mock search
        search_file_mock = MagicMock(side_effect=[
            [folder_mock],  # root folder
            [folder_mock],  # date folder
            []  # file
        ])

        # act
        with patch("camguard.gdrive_storage.GoogleDrive", return_value=gdrive_mock),\
                patch("camguard.gdrive_storage.GDriveStorage._search_file",
                      search_file_mock):
            GDriveStorage.upload(file)

        # assert
        create_file_dict = {
            'title': file,
            'mimeType': GDriveMimetype.JPEG.value,
            'parents': [{'id': "folder_id"}]
        }
        gdrive_mock.CreateFile.assert_called_with(create_file_dict)


class GDriveUploadManagerTest(TestCase):
    @patch("camguard.gdrive_storage.GDriveStorage.upload")
    @patch("camguard.gdrive_storage.GDriveStorageAuth.login", MagicMock())
    def test_should_enqueue_files(self, upload_mock: MagicMock):
        # arrange
        sut = GDriveStorage()
        file = "capture1.jpeg"

        # act
        sut.start()
        sut.enqueue_files([file])
        sleep(1.0)  # worker stop event check is between 100ms and 500ms
        sut.stop()

        # assert
        upload_mock.assert_called()
