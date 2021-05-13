import logging
import os
import time
from datetime import date
from os import path
from typing import List

# picamera cannot be installed on a non-pi system
from picamera import PiCamera  # type: ignore reportMissingImports

from .bridge import MotionHandlerImpl
from .exceptions import ConfigurationError


class RecordPathError(Exception):

    def __init__(self, message) -> None:
        self.message = message


LOGGER = logging.getLogger(__name__)


class RaspiCam(MotionHandlerImpl):
    """Class for wrapping python camera
    """

    def __init__(self, record_root_path: str, record_file_name: str = 'capture',
                 record_interval_sec: float = 1.0, record_count: int = 15) -> None:
        """ctor

        Args:
            record_root_path (str): root path where recorded pictures should be saved
            record_file_name (str, optional): record file name. Defaults to 'capture'.
            record_interval_sec (float, optional): interval seconds in which pictures 
            should be taken. Defaults to 1.
            record_count (int, optional): count of picture which should be recorded. 
            Defaults to 15.
        """
        LOGGER.debug(f"Configuring picamera with params: "
                     f"record_root_path: {record_root_path} "
                     f"record_file_name: {record_file_name} "
                     f"record_interval_sec: {record_interval_sec} "
                     f"record_count: {record_count}")
        super().__init__()

        self.record_root_path: str = record_root_path
        self.record_file_name: str = record_file_name
        self.record_interval_sec: float = record_interval_sec
        self.record_picture_count: int = record_count
        self._shutdown: bool = False

    def handle_motion(self) -> None:
        LOGGER.debug(f"Triggered by motion")
        with PiCamera() as pi_camera:
            recorded_pics: List[str] = self._record_picture(pi_camera)
            if self.after_handling:
                self.after_handling(recorded_pics)

    def shutdown(self) -> None:
        """shutdown picam recording 
        """
        LOGGER.info(f"Shutting down")
        self._shutdown = True
        self.after_handling = None

    def _record_picture(self, pi_camera) -> List[str]:
        """ record picture to given file_path

        Raises:
            ConfigurationError: if record_root_path is :None: or not an directory

        Returns:
            Sequence[str]: list of recorded file paths
        """
        if self._shutdown:
            return

        LOGGER.info("Recording pictures")

        if self.record_root_path is None or not path.isdir(self.record_root_path):
            raise ConfigurationError("Record root path invalid")

        # create directory with the current date
        date_str: str = date.today().strftime("%Y%m%d/")
        record_path: str = os.path.join(self.record_root_path, date_str)

        if not path.exists(record_path):
            os.mkdir(record_path)

        recorded = []
        for i, filename in enumerate(
                pi_camera.capture_continuous(f"{record_path}" +
                                             "{counter:03d}_{timestamp:%y%m%d_%H%M%S}_" +
                                             f"{self.record_file_name}.jpg")):
            LOGGER.info(f"Recorded picture to {filename}")
            recorded.append(filename)
            if self._shutdown:
                LOGGER.debug("Record interrupted by shutdown")
                break

            time.sleep(self.record_interval_sec)
            if i == self.record_picture_count - 1:
                break

        LOGGER.info("Finished recording")
        return recorded
