from unittest import TestCase
from unittest.mock import MagicMock, PropertyMock, create_autospec, patch

from camguard.bridge_api import (FileStorage, MotionDetector, MotionHandler)
from camguard.bridge_impl import FileStorageImpl, MotionDetectorImpl, MotionHandlerImpl
from camguard.settings import (FileStorageSettings, ImplementationType,
                               MotionDetectorSettings, MotionHandlerSettings,
                               Settings)


class MotionHandlerTest(TestCase):

    def setUp(self) -> None:
        self.record_root_path = "record_root"
        self.sut = MotionHandler(self.record_root_path)

    def test_should_load_dummy_settings_on_init(self):
        # arrange
        mh_settings_mock = create_autospec(spec=MotionHandlerSettings, spec_set=True)
        type(mh_settings_mock).impl_type = PropertyMock(
            return_value=ImplementationType.DUMMY)
        # settings should return MotionHandlerSettings mock on load_settings
        settings_mock = create_autospec(spec=Settings)
        settings_mock.load_settings = MagicMock(return_value=mh_settings_mock)
        # DummyCam mock
        dummy_cam_mock = MagicMock()
        dummy_cam_mock.DummyCam = MagicMock()

        # act
        with patch("camguard.bridge_api.MotionHandlerSettings", settings_mock), \
                patch.dict("sys.modules", {"camguard.dummy_cam": dummy_cam_mock}):
            self.sut.init()

        # assert
        dummy_cam_mock.DummyCam.assert_called_with(self.record_root_path)  # type: ignore
        settings_mock.load_settings.assert_called()

    def test_should_load_raspi_settings_on_init(self):
        # arrange
        mh_settings_mock = create_autospec(spec=MotionHandlerSettings, spec_set=True)
        type(mh_settings_mock).impl_type = PropertyMock(
            return_value=ImplementationType.RASPI)
        # settings should return MotionHandlerSettings mock on load_settings
        settings_mock = create_autospec(spec=Settings)
        settings_mock.load_settings = MagicMock(return_value=mh_settings_mock)
        # DummyCam mock
        raspi_cam_mock = MagicMock()
        raspi_cam_mock.RaspiCam = MagicMock()

        # act
        with patch("camguard.bridge_api.MotionHandlerSettings", settings_mock), \
                patch.dict("sys.modules", {"camguard.raspi_cam": raspi_cam_mock}):
            self.sut.init()

        # assert
        raspi_cam_mock.RaspiCam.assert_called_with(self.record_root_path)  # type: ignore
        settings_mock.load_settings.assert_called()

    def test_should_handle_motion(self):
        # arrange
        get_impl_mock = create_autospec(spec=MotionHandlerImpl, spec_set=True)
        detector_mock = create_autospec(spec=MotionDetector, spec_set=True)

        # act
        with patch("camguard.bridge_api.MotionHandler._get_impl",
                   return_value=get_impl_mock):
            self.sut.on_motion([]).send(detector_mock)

        # assert
        get_impl_mock.handle_motion.assert_called()

    def test_should_shutdown_on_stop(self):
        # arrange
        get_impl_mock = create_autospec(spec=MotionHandlerImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.MotionHandler._get_impl",
                   return_value=get_impl_mock):
            self.sut.stop()

        # assert
        get_impl_mock.shutdown.assert_called()


class MotionDetectorTest(TestCase):
    def setUp(self) -> None:
        self.gpio_pin = 23
        self.sut = MotionDetector(self.gpio_pin)

    def test_should_load_dummy_settings_on_init(self):
        # arrange
        md_settings_mock = create_autospec(spec=MotionDetectorSettings, spec_set=True)
        type(md_settings_mock).impl_type = PropertyMock(
            return_value=ImplementationType.DUMMY)
        # settings should return MotionDetectorSettings mock on load_settings
        settings_mock = create_autospec(spec=Settings)
        settings_mock.load_settings = MagicMock(return_value=md_settings_mock)
        # DummyCam mock
        dummy_sensor_mock = MagicMock()
        dummy_sensor_mock.DummyGpioSensor = MagicMock()

        # act
        with patch("camguard.bridge_api.MotionDetectorSettings", settings_mock), \
                patch.dict("sys.modules", {"camguard.dummy_gpio_sensor": dummy_sensor_mock}):
            self.sut.init()

        # assert
        dummy_sensor_mock.DummyGpioSensor.assert_called_with(self.gpio_pin)  # type: ignore
        settings_mock.load_settings.assert_called()

    def test_should_load_raspi_settings_on_init(self):
        # arrange
        md_settings_mock = create_autospec(spec=MotionDetectorSettings, spec_set=True)
        type(md_settings_mock).impl_type = PropertyMock(
            return_value=ImplementationType.RASPI)
        # settings should return MotionDetectorSettings mock on load_settings
        settings_mock = create_autospec(spec=Settings)
        settings_mock.load_settings = MagicMock(return_value=md_settings_mock)
        # DummyCam mock
        gpio_sensor_mock = MagicMock()
        gpio_sensor_mock.RaspiGpioSensor = MagicMock()

        # act
        with patch("camguard.bridge_api.MotionDetectorSettings", settings_mock), \
                patch.dict("sys.modules", {"camguard.raspi_gpio_sensor": gpio_sensor_mock}):
            self.sut.init()

        # assert
        gpio_sensor_mock.RaspiGpioSensor.assert_called_with(self.gpio_pin)  # type: ignore
        settings_mock.load_settings.assert_called()

    def test_should_shutdown_on_stop(self):
        # arrange
        get_impl_mock = create_autospec(spec=MotionDetectorImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.MotionDetector._get_impl",
                   return_value=get_impl_mock):
            self.sut.stop()

        # assert
        get_impl_mock.shutdown.assert_called()

    def test_should_register_handlers(self):
        # arrange
        get_impl_mock = create_autospec(spec=MotionDetectorImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.MotionDetector._get_impl",
                   return_value=get_impl_mock):
            self.sut.register_handlers([])

        # assert
        get_impl_mock.register_handler.assert_called()


class FileStorageTest(TestCase):
    def test_should_load_dummy_settings(self):
        # arrange
        fs_settings_mock = create_autospec(spec=FileStorageSettings, spec_set=True)
        type(fs_settings_mock).impl_type = PropertyMock(
            return_value=ImplementationType.DUMMY)
        # settings should return FileStorageSettings mock on load_settings
        settings_mock = create_autospec(spec=Settings)
        settings_mock.load_settings = MagicMock(return_value=fs_settings_mock)
        # DummyCam mock
        dummy_storage_mock = MagicMock()
        dummy_storage_mock.GDriveDummyStorage = MagicMock()

        # act
        with patch("camguard.bridge_api.FileStorageSettings", settings_mock), \
                patch.dict("sys.modules", {"camguard.gdrive_dummy_storage": dummy_storage_mock}):
            FileStorage()._get_impl()  # type: ignore

        # assert
        dummy_storage_mock.GDriveDummyStorage.assert_called()  # type: ignore
        settings_mock.load_settings.assert_called()

    def test_should_load_gdrive_settings(self):
        # arrange
        fs_settings_mock = create_autospec(spec=FileStorageSettings, spec_set=True)
        type(fs_settings_mock).impl_type = PropertyMock(
            return_value=None)
        # settings should return FileStorageSettings mock on load_settings
        settings_mock = create_autospec(spec=Settings)
        settings_mock.load_settings = MagicMock(return_value=fs_settings_mock)
        # DummyCam mock
        gdrive_storage_mock = MagicMock()
        gdrive_storage_mock.GDriveStorage = MagicMock()

        # act
        with patch("camguard.bridge_api.FileStorageSettings", settings_mock), \
                patch.dict("sys.modules",
                           {"camguard.gdrive_storage": gdrive_storage_mock}):
            FileStorage()._get_impl()  # type: ignore

        # assert
        gdrive_storage_mock.GDriveStorage.assert_called()  # type: ignore
        settings_mock.load_settings.assert_called()

    @patch("camguard.bridge_api.FileStorageSettings.load_settings", MagicMock())
    def test_should_authenticate(self):
        # arrange
        get_impl_mock = create_autospec(spec=FileStorageImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.FileStorage._get_impl",
                   return_value=get_impl_mock):
            FileStorage().authenticate()

        # assert
        get_impl_mock.authenticate.assert_called()

    @patch("camguard.bridge_api.FileStorageSettings.load_settings", MagicMock())
    def test_should_start(self):
        # arrange
        get_impl_mock = create_autospec(spec=FileStorageImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.FileStorage._get_impl",
                   return_value=get_impl_mock):
            FileStorage().start()

        # assert
        get_impl_mock.start.assert_called()

    @patch("camguard.bridge_api.FileStorageSettings.load_settings", MagicMock())
    def test_should_stop(self):
        # arrange
        get_impl_mock = create_autospec(spec=FileStorageImpl, spec_set=True)

        # act
        with patch("camguard.bridge_api.FileStorage._get_impl",
                   return_value=get_impl_mock):
            FileStorage().stop()

        # assert
        get_impl_mock.stop.assert_called()

    @patch("camguard.bridge_api.FileStorageSettings.load_settings", MagicMock())
    def test_should_enqueue_files(self):
        # arrange
        get_impl_mock = create_autospec(spec=FileStorageImpl, spec_set=True)
        files = ["file1", "file2"]

        # act
        with patch("camguard.bridge_api.FileStorage._get_impl",
                   return_value=get_impl_mock):
            FileStorage().enqueue_files().send(files)

        # assert
        get_impl_mock.enqueue_files.assert_called_with(files)
