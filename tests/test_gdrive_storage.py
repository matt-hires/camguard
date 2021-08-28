import datetime
from time import sleep
from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, call, create_autospec, mock_open, patch

from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from googleapiclient.discovery import build # type: ignore
from googleapiclient.http import MediaFileUpload # type: ignore

from camguard.exceptions import GDriveError
from camguard.file_storage_settings import GDriveStorageSettings
from camguard.gdrive_storage import (GDriveMimetype, GDriveStorage,
                                     GDriveStorageAuth)


class GDriveStorageAuthTest(TestCase):

    @patch("camguard.gdrive_storage.path.exists", MagicMock(return_value=False))
    @patch("camguard.gdrive_storage.open", mock_open())
    def test_should_authenticate_without_token(self):
        # arrange
        storage_settings_mock = create_autospec(spec=GDriveStorageSettings, spec_set=True)
        type(storage_settings_mock).oauth_token_path = PropertyMock(return_value=".")
        type(storage_settings_mock).oauth_credentials_path = PropertyMock(return_value=".")

        # act
        with patch("camguard.gdrive_storage.InstalledAppFlow",
                   # due to the classmethod 'from_client_secrets_file' it's necessary to
                   # create the mock inline
                   return_value=create_autospec(spec=InstalledAppFlow,
                                                spec_set=True)) as app_flow_mock:
            GDriveStorageAuth.authenticate(storage_settings_mock)

            # assert
            app_flow_mock.from_client_secrets_file.assert_called()  # type: ignore


class GDriveStorageTest(TestCase):

    def setUp(self) -> None:
        # mock GDriveStorageAuth
        self._gdrive_auth_mock = create_autospec(spec=GDriveStorageAuth, spec_set=True)
        # mock GDriveStorageSettings
        self._storage_settings_mock = create_autospec(spec=GDriveStorageSettings, spec_set=True, )
        # mock Google Drive API build function
        self._googleapi_service_mock = MagicMock()
        self._googleapi_build_mock = create_autospec(
            spec=build, spec_set=True, name='googleapi_build_mock', return_value=self._googleapi_service_mock)
        type(self._storage_settings_mock).upload_folder_name = PropertyMock(return_value="Camguard")

        self._media_file_mock = create_autospec(spec=MediaFileUpload, spec_set=True)
        self._patcher = patch.multiple("camguard.gdrive_storage",
                                       build=self._googleapi_build_mock,
                                       # ctor mock proxy
                                       MediaFileUpload=MagicMock(return_value=self._media_file_mock),
                                       GDriveStorageAuth=self._gdrive_auth_mock,
                                       GDriveStorageSettings=self._storage_settings_mock)
        self._patcher.start()
        self.sut = GDriveStorage(self._storage_settings_mock)

    @patch("camguard.gdrive_storage.GDriveStorage._search_file", MagicMock(return_value=[]))
    def test_should_create_root(self):
        # arrange

        # mock root folder query
        create_folder_dict = {
            'name': self.sut._upload_folder_name,  # type: ignore
            'mimeType': GDriveMimetype.FOLDER.value,
            'parents': ['root']
        }
        file = "capture1.jpeg"

        # act
        self.sut.upload(file)

        # assert
        self._googleapi_service_mock.assert_has_calls(
            [call.__enter__().files().create(body=create_folder_dict, fields='id, name, parents')], any_order=True)

    @patch("camguard.gdrive_storage.GDriveStorage._search_file", MagicMock(return_value=[MagicMock(), MagicMock()]))
    def test_should_raise_error_when_more_than_one_root_found(self):
        # arrange
        file = "capture1.jpeg"

        # act
        with self.assertRaises(GDriveError):
            self.sut.upload(file)

        # assert
        self._googleapi_service_mock.assert_not_called()

    def test_should_create_date_folder(self):
        # arrange
        file = "capture1.jpeg"
        # mock root folder query
        root_folder = MagicMock()
        root_folder.__getitem__ = MagicMock(key="id", return_value="camguard_id")
        search_file_mock = MagicMock(side_effect=[
            [root_folder],  # root folder
            [],  # date folder
            []  # file
        ])

        # act
        with patch("camguard.gdrive_storage.GDriveStorage._search_file", search_file_mock):
            self.sut.upload(file)

        # assert
        date_str = datetime.date.today().strftime("%Y%m%d")
        create_folder_dict = {
            'name': date_str,
            'mimeType': GDriveMimetype.FOLDER.value,
            'parents': ['camguard_id']
        }
        self._googleapi_service_mock.assert_has_calls(
            [call.__enter__().files().create(body=create_folder_dict, fields='id, name, parents')], any_order=True)

    def test_should_upload_file(self):
        # arrange
        file = "capture1.jpeg"
        folder_mock = MagicMock()
        folder_mock.__getitem__ = MagicMock(key="id", return_value="folder_id")
        # mock search
        search_file_mock = MagicMock(side_effect=[
            [folder_mock],  # root folder
            [folder_mock],  # date folder
            []  # file
        ])

        # act
        with patch("camguard.gdrive_storage.GDriveStorage._search_file", search_file_mock):
            self.sut.upload(file)

        # assert
        create_file_dict = {
            'name': file,
            'parents': ["folder_id"]
        }
        self._googleapi_service_mock.assert_has_calls(
            [call.__enter__().files().create(body=create_file_dict,
                                             media_body=self._media_file_mock,
                                             fields='id, name, parents')], any_order=True)

        # self._gdrive_mock.CreateFile.assert_called_with(create_file_dict)

    def tearDown(self) -> None:
        self._patcher.stop()


class GDriveUploadManagerTest(TestCase):
    @patch("camguard.gdrive_storage.GDriveStorage.upload")
    @patch("camguard.gdrive_storage.GDriveStorageAuth.authenticate", MagicMock())
    def test_should_enqueue_files(self, upload_mock: MagicMock):
        # arrange
        # mock GDriveStorageSettings
        storage_settings_mock = create_autospec(spec=GDriveStorageSettings, spec_set=True)
        type(storage_settings_mock).upload_folder_name = PropertyMock(return_value="Camguard")
        sut = GDriveStorage(storage_settings_mock)
        file = "capture1.jpeg"

        # act
        sut.start()
        sut.enqueue_files([file])
        sleep(1.0)  # worker stop event check is between 100ms and 500ms
        sut.stop()

        # assert
        upload_mock.assert_called()
