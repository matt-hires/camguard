import logging
import os
import time
from datetime import date
from os import path
from typing import Sequence

# picamera cannot be installed on a non-pi system
from picamera import PiCamera # type: ignore reportMissingImports
from .errors import ConfigurationError


class RecordPathError(Exception):

    def __init__(self, message):
        self.message = message


LOGGER = logging.getLogger(__name__)


class CamFacade:
    """Class for wrapping python camera
    """

    def __init__(self, record_root_path: str, record_file_name: str = 'capture',
                 record_interval_sec: int = 1, record_count: int = 15):
        """ctor

        Args:
            record_root_path (str): root path where recorded pictures should be safed
            record_file_name (str, optional): record file name. Defaults to 'capture'.
            record_interval_sec (int, optional): interval seconds in which pictures 
            should be taken. Defaults to 1.
            record_count (int, optional): count of picture which should be recorded. 
            Defaults to 15.
        """
        LOGGER.debug(f"Configuring picamera with params: "
                     f"record_root_path: {record_root_path} "
                     f"record_file_name: {record_file_name} "
                     f"record_interval_sec: {record_interval_sec} "
                     f"record_count: {record_count}")

        self.record_root_path = record_root_path
        self.record_file_name = record_file_name
        self.record_interval_sec = record_interval_sec
        self.record_picture_count = record_count
        self._shutdown = False

    def record_picture(self) -> Sequence[str]:
        """ record picture to given file_path

        Raises:
            ConfigurationError: if record_root_path is :None: or not an directory

        Returns:
            Sequence[str]: list of recorded file paths
        """
        with PiCamera() as pi_camera:
            LOGGER.info("Recording pictures")

            if self.record_root_path is None or not path.isdir(self.record_root_path):
                raise ConfigurationError("Record root path invalid")

            # create directory with the current date
            date_str = date.today().strftime("%Y%m%d/")
            record_path = os.path.join(self.record_root_path, date_str)

            if not path.exists(record_path):
                os.mkdir(record_path)

            recorded = []
            for i, filename in enumerate(
                    pi_camera.capture_continuous(f"{record_path}" +
                                                 "{counter:03d}_{timestamp:%y%m%d_%H%M%S}_" +
                                                 f"{self.record_file_name}.jpg")):

                LOGGER.debug(f"Recorded picture to {filename}")
                recorded.append(filename)
                if self._shutdown:
                    LOGGER.debug("Record interrupted by shutdown")
                    break

                time.sleep(self.record_interval_sec)
                if i == self.record_picture_count - 1:
                    break

            LOGGER.info("Finished recording")
            return recorded

    def shutdown(self) -> None:
        LOGGER.debug(f"Shutting down")
        self._shutdown = True
