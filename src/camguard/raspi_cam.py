import logging
import os
import time
from datetime import date
from typing import Any, ClassVar, List

# picamera cannot be installed on a non-pi system
from picamera import PiCamera  # type: ignore reportMissingImports

from camguard.motion_handler_settings import RaspiCamSettings
from camguard.bridge_impl import MotionHandlerImpl


LOGGER = logging.getLogger(__name__)


class RaspiCam(MotionHandlerImpl):
    """Class for wrapping python camera
    """
    _id: ClassVar[int] = 0

    def __init__(self, settings: RaspiCamSettings) -> None:
        self._settings = settings
        self._shutdown: bool = False
        RaspiCam._id += 1

    def handle_motion(self) -> Any:
        LOGGER.debug("Triggered by motion")
        with PiCamera() as pi_camera:  # type: ignore
            return self._record_picture(pi_camera)

    def shutdown(self) -> None:
        """shutdown picam recording 
        """
        LOGGER.info("Shutting down")
        self._shutdown = True

    def _record_picture(self, pi_camera: Any) -> List[str]:
        """ record picture to given file_path

        Raises:
            ConfigurationError: if record_root_path is :None: or not an directory

        Returns:
            List[str]: list of recorded file paths
        """
        if self._shutdown:
            # do not record if shutdown was triggered
            return []

        LOGGER.info("Recording pictures")

        # expand env variables and '~' in path
        resolved_path = os.path.expandvars(os.path.expanduser(self._settings.record_path))

        # create directory with the current date
        date_str = date.today().strftime('%Y%m%d/')
        record_path = os.path.join(resolved_path, date_str)

        if not os.path.exists(record_path):
            os.makedirs(record_path, exist_ok=True)

        recorded: List[str] = []
        for i, filename in enumerate(
                pi_camera.capture_continuous(record_path + self._settings.record_file_format)):
            LOGGER.info(f"Recorded picture to {filename}")
            recorded.append(filename)
            if self._shutdown:
                LOGGER.debug("Record interrupted by shutdown")
                break

            time.sleep(self._settings.record_interval_sec)
            if i == self._settings.record_count - 1:
                break

        LOGGER.info("Finished recording")
        return recorded

    @property
    def id(self) -> int:
        return RaspiCam._id
