import logging
import time
from os import path

from picamera import PiCamera

from camguard.exceptions.input_error import InputError


class RecordPathError(Exception):

    def __init__(self, message):
        self.message = message


LOGGER = logging.getLogger(__name__)


class CamAdapter:
    """
    Adapter class for wrapping python camera
    """

    def __init__(self, record_root_path: str, record_file_name: str = 'capture',
                 record_interval_sec: int = 1, record_count: int = 15):
        """
        default ctor

        :param record_root_path: root path where recorded pictures should be safed
        :param record_file_name: record file name
        :param record_interval_sec: interval seconds in which pictures should be taken (default is 1)
        :param record_count: count of picture which should be recorded (default is 15)
        """
        LOGGER.debug(f"Configuring picamera with params: "
                     f"record_root_path: {record_root_path} "
                     f"record_file_name: {record_file_name} "
                     f"record_interval_sec: {record_interval_sec} "
                     f"record_count: {record_count}")

        self.__record_root_path = record_root_path
        self.__record_file_name = record_file_name
        self.__record_interval_sec = record_interval_sec
        self.__record_picture_count = record_count

    def record_picture(self) -> None:
        """
        record picture to given file_path
        :raises: :NotADirectoryError: if record_root_path is :None: or not an directory
        """
        with PiCamera() as pi_camera:
            LOGGER.info("Recording picture...")

            if self.record_root_path is None or not path.isdir(self.record_root_path):
                raise InputError("Record root path invalid")

            for i, filename in enumerate(
                    pi_camera.capture_continuous(f"{self.record_root_path}" +
                                                 "{counter:03d}_{timestamp:%y%m%d_%H%M%S}_" +
                                                 f"{self.record_file_name}.jpg")):
                LOGGER.debug(f"Recording picture to {filename}...")
                time.sleep(self.record_interval_sec)
                if i == self.record_picture_count - 1:
                    break

    @property
    def record_file_name(self) -> str:
        return self.__record_file_name

    @record_file_name.setter
    def record_file_name(self, file_name) -> None:
        self.__record_file_name = file_name

    @property
    def record_root_path(self) -> str:
        return self.__record_root_path

    @record_root_path.setter
    def record_root_path(self, value: str) -> None:
        self.__record_root_path = value

    @property
    def record_picture_count(self) -> int:
        return self.__record_picture_count

    @record_picture_count.setter
    def record_picture_count(self, value: int) -> None:
        self.__record_picture_count = value

    @property
    def record_interval_sec(self) -> int:
        return self.__record_interval_sec

    @record_interval_sec.setter
    def record_interval_sec(self, value: int) -> None:
        self.__record_interval_sec = value
