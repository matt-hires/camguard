from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch

from camguard.bridge_api import FileStorage, MailClient, MotionDetector, MotionHandler
from camguard.bridge_impl import (FileStorageImpl, MailClientImpl, MotionDetectorImpl,
                                  MotionHandlerImpl)

from camguard.settings import ImplementationType
from camguard.file_storage_settings import DummyGDriveStorageSettings, FileStorageSettings, GDriveStorageSettings
from camguard.mail_client_settings import MailClientSettings, DummyMailClientSettings
from camguard.motion_handler_settings import MotionHandlerSettings, DummyCamSettings, RaspiCamSettings
from camguard.motion_detector_settings import MotionDetectorSettings, DummyGpioSensorSettings, RaspiGpioSensorSettings


class MotionHandlerTest(TestCase):

    def setUp(self) -> None:
        # MotionhandlerSettings
        self._mh_settings_mock = create_autospec(spec=MotionHandlerSettings, spec_set=True)
        type(self._mh_settings_mock).impl_type = PropertyMock(return_value=ImplementationType.DUMMY)
        # settings should return MotionHandlerSettings mock on load_settings
        self._mh_settings_mock.load_settings = MagicMock(return_value=self._mh_settings_mock)

        # DummyCamSettings
        self._dummy_cam_settings_mock = create_autospec(spec=DummyCamSettings, spec_set=True)
        self._dummy_cam_settings_mock.load_settings = MagicMock(return_value=self._dummy_cam_settings_mock)

        self._patcher = patch.multiple("camguard.bridge_api",
                                       MotionHandlerSettings=self._mh_settings_mock,
                                       DummyCamSettings=self._dummy_cam_settings_mock)
        self._patcher.start()
        self._config_path = "."

        # motion handler mocked with dummy cam settings by default
        self.sut = MotionHandler(self._config_path)

    def test_should_load_dummy_settings_on_init(self):
        # arrange
        # DummyCam
        dummy_cam_mock = MagicMock()
        dummy_cam_mock.DummyCam = MagicMock()

        # act
        with patch.dict("sys.modules", {"camguard.dummy_cam": dummy_cam_mock}):
            MotionHandler(self._config_path)

        # assert
        dummy_cam_mock.DummyCam.assert_called_with(self._dummy_cam_settings_mock)  # type: ignore
        self._mh_settings_mock.load_settings.assert_called_with(self._config_path)
        self._dummy_cam_settings_mock.load_settings.assert_called_with(self._config_path)

    def test_should_load_raspi_settings_on_init(self):
        # arrange

        # MotionhandlerSettings
        mh_settings_mock = create_autospec(spec=MotionHandlerSettings, spec_set=True)
        type(mh_settings_mock).impl_type = PropertyMock(return_value=ImplementationType.RASPI)
        # settings should return MotionHandlerSettings mock on load_settings
        mh_settings_mock.load_settings = MagicMock(return_value=mh_settings_mock)

        # RaspiCamSettings
        raspi_cam_settings_mock = create_autospec(spec=RaspiCamSettings, spec_set=True)
        raspi_cam_settings_mock.load_settings = MagicMock(return_value=raspi_cam_settings_mock)

        # RaspiCam
        raspi_cam_mock = MagicMock()
        raspi_cam_mock.RaspiCam = MagicMock()

        # act
        with patch("camguard.bridge_api.MotionHandlerSettings", mh_settings_mock), \
                patch("camguard.bridge_api.RaspiCamSettings", raspi_cam_settings_mock), \
                patch.dict("sys.modules", {"camguard.raspi_cam": raspi_cam_mock}):
            MotionHandler(self._config_path)

        # assert
        raspi_cam_mock.RaspiCam.assert_called_with(raspi_cam_settings_mock)  # type: ignore
        mh_settings_mock.load_settings.assert_called_with(self._config_path)
        raspi_cam_settings_mock.load_settings.assert_called_with(self._config_path)

    def test_should_handle_motion(self):
        # arrange
        get_impl_mock = create_autospec(spec=MotionHandlerImpl, spec_set=True)
        detector_mock = create_autospec(spec=MotionDetector, spec_set=True)

        # act
        with patch("camguard.bridge_api.MotionHandler._get_impl", return_value=get_impl_mock):
            self.sut.on_motion([]).send(detector_mock)

        # assert
        get_impl_mock.handle_motion.assert_called()

    def test_should_shutdown_on_stop(self):
        # arrange
        get_impl_mock = create_autospec(spec=MotionHandlerImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.MotionHandler._get_impl", return_value=get_impl_mock):
            self.sut.stop()

        # assert
        get_impl_mock.shutdown.assert_called()

    def tearDown(self) -> None:
        self._patcher.stop()


class MotionDetectorTest(TestCase):
    def setUp(self) -> None:
        # MotionDetectorSettings
        self._md_settings_mock = create_autospec(spec=MotionDetectorSettings, spec_set=True)
        type(self._md_settings_mock).impl_type = PropertyMock(return_value=ImplementationType.DUMMY)
        # settings should return MotionDetectorSettings mock on load_settings
        self._md_settings_mock.load_settings = MagicMock(return_value=self._md_settings_mock)

        # DummyGpioSensorSettings
        self._dummy_sensor_settings_mock = create_autospec(spec=DummyGpioSensorSettings, spec_set=True)
        self._dummy_sensor_settings_mock.load_settings = MagicMock(return_value=self._dummy_sensor_settings_mock)

        self._patcher = patch.multiple("camguard.bridge_api",
                                       MotionDetectorSettings=self._md_settings_mock,
                                       DummyGpioSensorSettings=self._dummy_sensor_settings_mock)
        self._patcher.start()
        self._config_path = "."
        # motion detector mocked with dummy gpio sensor settings by default
        self.sut = MotionDetector(self._config_path)

    def test_should_load_dummy_settings_on_init(self):
        # arrange
        # DummyGpioSensor
        dummy_sensor_mock = MagicMock()
        dummy_sensor_mock.DummyGpioSensor = MagicMock()

        # act
        with patch.dict("sys.modules", {"camguard.dummy_gpio_sensor": dummy_sensor_mock}):
            MotionDetector(self._config_path)

        # assert
        dummy_sensor_mock.DummyGpioSensor.assert_called_with(self._dummy_sensor_settings_mock)  # type: ignore
        self._md_settings_mock.load_settings.assert_called_with(self._config_path)
        self._dummy_sensor_settings_mock.load_settings.assert_called_with(self._config_path)

    def test_should_load_raspi_settings_on_init(self):
        # arrange
        # MotionDetectorSettings
        md_settings_mock = create_autospec(spec=MotionDetectorSettings, spec_set=True)
        type(md_settings_mock).impl_type = PropertyMock(return_value=ImplementationType.RASPI)
        # settings should return MotionHandlerSettings mock on load_settings
        md_settings_mock.load_settings = MagicMock(return_value=md_settings_mock)

        # RaspiGpioSensorSettings
        raspi_sensor_settings_mock = create_autospec(spec=RaspiGpioSensorSettings, spec_set=True)
        raspi_sensor_settings_mock.load_settings = MagicMock(return_value=raspi_sensor_settings_mock)

        # RaspiGpioSensor
        raspi_sensor_mock = MagicMock()
        raspi_sensor_mock.RaspiGpioSensor = MagicMock()

        # act
        with patch("camguard.bridge_api.MotionDetectorSettings", md_settings_mock), \
                patch("camguard.bridge_api.RaspiGpioSensorSettings", raspi_sensor_settings_mock), \
                patch.dict("sys.modules", {"camguard.raspi_gpio_sensor": raspi_sensor_mock}):
            MotionDetector(self._config_path)

        # assert
        raspi_sensor_mock.RaspiGpioSensor.assert_called_with(raspi_sensor_settings_mock)  # type: ignore
        md_settings_mock.load_settings.assert_called_with(self._config_path)
        raspi_sensor_settings_mock.load_settings.assert_called_with(self._config_path)

    def test_should_shutdown_on_stop(self):
        # arrange
        get_impl_mock = create_autospec(spec=MotionDetectorImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.MotionDetector._get_impl", return_value=get_impl_mock):
            self.sut.stop()

        # assert
        get_impl_mock.shutdown.assert_called()

    def test_should_register_handlers(self):
        # arrange
        get_impl_mock = create_autospec(spec=MotionDetectorImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.MotionDetector._get_impl", return_value=get_impl_mock):
            self.sut.register_handlers([])

        # assert
        get_impl_mock.register_handler.assert_called()

    def tearDown(self) -> None:
        self._patcher.stop()


class FileStorageTest(TestCase):

    def setUp(self) -> None:
        # FileStorageSettings
        self._fs_settings_mock = create_autospec(spec=FileStorageSettings, spec_set=True)
        type(self._fs_settings_mock).impl_type = PropertyMock(return_value=ImplementationType.DUMMY)
        # settings should return FileStorageSettings mock on load_settings
        self._fs_settings_mock.load_settings = MagicMock(return_value=self._fs_settings_mock)

        # DummyGDriveStorageSettings
        self._dummy_storage_settings_mock = create_autospec(spec=DummyGDriveStorageSettings, spec_set=True)
        self._dummy_storage_settings_mock.load_settings = MagicMock(return_value=self._dummy_storage_settings_mock)

        self._patcher = patch.multiple("camguard.bridge_api",
                                       FileStorageSettings=self._fs_settings_mock,
                                       DummyGDriveStorageSettings=self._dummy_storage_settings_mock)
        self._patcher.start()
        self._config_path = "."
        # file storage mocked with dummy gdrive storage settings by default
        self.sut = FileStorage(self._config_path)

    def test_should_load_dummy_settings(self):
        # arrange
        # Dummy storage mock
        dummy_storage_mock = MagicMock()
        dummy_storage_mock.DummyGDriveStorage = MagicMock()

        # act
        with patch.dict("sys.modules", {"camguard.dummy_gdrive_storage": dummy_storage_mock}):
            FileStorage(self._config_path)

        # assert
        dummy_storage_mock.DummyGDriveStorage.assert_called()  # type: ignore
        self._fs_settings_mock.load_settings.assert_called_with(self._config_path)
        self._dummy_storage_settings_mock.load_settings.assert_called_with(self._config_path)

    def test_should_load_gdrive_settings(self):
        # arrange
        # FileStorageSettings
        fs_settings_mock = create_autospec(spec=FileStorageSettings, spec_set=True)
        type(fs_settings_mock).dummy_impl = PropertyMock(return_value=False)
        # settings should return MotionHandlerSettings mock on load_settings
        fs_settings_mock.load_settings = MagicMock(return_value=fs_settings_mock)

        # RaspiGpioSensorSettings
        gdrive_storage_settings_mock = create_autospec(spec=GDriveStorageSettings, spec_set=True)
        gdrive_storage_settings_mock.load_settings = MagicMock(return_value=gdrive_storage_settings_mock)
        # GDriveStorage mock
        gdrive_storage_mock = MagicMock()
        gdrive_storage_mock.GDriveStorage = MagicMock()

        # act
        with patch("camguard.bridge_api.FileStorageSettings", fs_settings_mock), \
                patch("camguard.bridge_api.GDriveStorageSettings", gdrive_storage_settings_mock), \
                patch.dict("sys.modules", {"camguard.gdrive_storage": gdrive_storage_mock}):
            FileStorage(self._config_path)

        # assert
        gdrive_storage_mock.GDriveStorage.assert_called_with(gdrive_storage_settings_mock)  # type: ignore
        fs_settings_mock.load_settings.assert_called_with(self._config_path)
        gdrive_storage_settings_mock.load_settings.assert_called_with(self._config_path)

    def test_should_authenticate(self):
        # arrange
        get_impl_mock = create_autospec(spec=FileStorageImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.FileStorage._get_impl", return_value=get_impl_mock):
            self.sut.authenticate()

        # assert
        get_impl_mock.authenticate.assert_called()

    def test_should_start(self):
        # arrange
        get_impl_mock = create_autospec(spec=FileStorageImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.FileStorage._get_impl", return_value=get_impl_mock):
            self.sut.start()

        # assert
        get_impl_mock.start.assert_called()

    def test_should_stop(self):
        # arrange
        get_impl_mock = create_autospec(spec=FileStorageImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.FileStorage._get_impl", return_value=get_impl_mock):
            self.sut.stop()

        # assert
        get_impl_mock.stop.assert_called()

    def test_should_enqueue_files(self):
        # arrange
        get_impl_mock = create_autospec(spec=FileStorageImpl, spec_set=True)
        files = ["file1", "file2"]

        # act
        with patch("camguard.bridge_api.FileStorage._get_impl", return_value=get_impl_mock):
            self.sut.enqueue_files().send(files)

        # assert
        get_impl_mock.enqueue_files.assert_called_with(files)

    def tearDown(self) -> None:
        self._patcher.stop()


class MailClientTest(TestCase):

    def setUp(self) -> None:
        # MailClientSettings
        self._mail_settings_mock = create_autospec(spec=MailClientSettings, spec_set=True)
        type(self._mail_settings_mock).impl_type = PropertyMock(return_value=ImplementationType.DUMMY)
        # settings should return MailClientSettings mock on load_settings
        self._mail_settings_mock.load_settings = MagicMock(return_value=self._mail_settings_mock)

        # DummyGDriveStorageSettings
        self._dummy_mail_settings_mock = create_autospec(spec=DummyMailClientSettings, spec_set=True)
        self._dummy_mail_settings_mock.load_settings = MagicMock(return_value=self._dummy_mail_settings_mock)

        self._patcher = patch.multiple("camguard.bridge_api",
                                       MailClientSettings=self._mail_settings_mock,
                                       DummyMailClientSettings=self._dummy_mail_settings_mock)
        self._patcher.start()
        self._config_path = "."
        self.sut = MailClient(self._config_path)

    def test_should_send_mail(self) -> None:
        # arrange
        get_impl_mock = create_autospec(spec=MailClientImpl, spec_set=True)
        files = ["file1", "file2"]

        # act
        with patch("camguard.bridge_api.MailClient._get_impl", return_value=get_impl_mock):
            self.sut.send_mail().send(files)

        # assert
        get_impl_mock.send_mail.assert_called_with(files)

    def tearDown(self) -> None:
        self._patcher.stop()
