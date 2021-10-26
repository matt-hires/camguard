
from typing import Any, ClassVar, Dict
from camguard.settings import Settings


class FileStorageSettings(Settings):
    """specialized file storage settings class
    """
    _DUMMY_IMPL: ClassVar[str] = "dummy_implementation"
    _KEY: ClassVar[str] = "file_storage"

    @property
    def dummy_impl(self) -> bool:
        return self._dummy_impl

    @dummy_impl.setter
    def dummy_impl(self, value: bool):
        self._dummy_impl = value

    def _parse_data(self, data: Dict[str, Any]):
        super()._parse_data(data)

        self.dummy_impl = super().get_setting_from_key(
            setting_key=f"{FileStorageSettings._KEY}.{FileStorageSettings._DUMMY_IMPL}",
            settings=data,
            default=False
        )


class GDriveStorageSettings(FileStorageSettings):
    """specialized gdrive storage setting
    """
    _UPLOAD_FOLDER_NAME: ClassVar[str] = "upload_folder_name"
    _KEY: ClassVar[str] = "gdrive_storage"
    _OAUTH_TOKEN_PATH: ClassVar[str] = "oauth_token_path"
    _OAUTH_CREDENTIALS_PATH: ClassVar[str] = "oauth_credentials_path"

    @property
    def upload_folder_name(self) -> str:
        """gdrive folder name for the upload, defaults to 'Camguard'
        """
        return self._upload_folder_name

    @upload_folder_name.setter
    def upload_folder_name(self, value: str) -> None:
        self._upload_folder_name = value

    @property
    def oauth_token_path(self) -> str:
        """oauth token root path for the 'token.json' file, defaults to the current directory
        """
        return self._oauth_token_path

    @oauth_token_path.setter
    def oauth_token_path(self, value: str) -> None:
        self._oauth_token_path = value

    @property
    def oauth_credentials_path(self) -> str:
        """oauth credentials root path for the 'credentials.json' file, defaults to current directory
        """
        return self._oauth_credentials_path

    @oauth_credentials_path.setter
    def oauth_credentials_path(self, value: str) -> None:
        self._oauth_credentials_path = value

    def _parse_data(self, data: Dict[str, Any]):
        """parse settings data for gpio gdrive storage settings
        take care: in here self._KEY is used for key, this can be a different value than GDriveStorageSettings._KEY,
        especially when using DummyGDriveStorageSettings where this value will be overwritten
        """
        super()._parse_data(data)

        self.upload_folder_name = super().get_setting_from_key(
            setting_key=f"{FileStorageSettings._KEY}.{self._KEY}.{GDriveStorageSettings._UPLOAD_FOLDER_NAME}",
            settings=data,
            default="Camguard"
        )

        self.oauth_token_path = super().get_setting_from_key(
            setting_key=f"{FileStorageSettings._KEY}.{self._KEY}.{GDriveStorageSettings._OAUTH_TOKEN_PATH}",
            settings=data,
            default="."
        )

        self.oauth_credentials_path = super().get_setting_from_key(
            setting_key=f"{FileStorageSettings._KEY}.{self._KEY}.{GDriveStorageSettings._OAUTH_CREDENTIALS_PATH}",
            settings=data,
            default="."
        )


class DummyGDriveStorageSettings(GDriveStorageSettings):
    """specialized gdrive dummy storage setting
    """
    _KEY: ClassVar[str] = "dummy_gdrive_storage"
