import logging
import time
from datetime import date, datetime
from typing import Any, ClassVar, List

from .bridge_impl import MotionHandlerImpl
from .settings import DummyCamSettings

LOGGER = logging.getLogger(__name__)


class DummyCam(MotionHandlerImpl):
    """dummy cam implementation
    this can be used for running camguard in a dummy mode
    """
    _id: ClassVar[int] = 0

    def __init__(self, settings: DummyCamSettings) -> None:
        """default ctor

        Args:
            settings (DummyCamSettings): dummy cam settings object
        """
        self._settings = settings
        self._shutdown: bool = False
        DummyCam._id += 1

    def handle_motion(self) -> Any:
        LOGGER.debug(f"Triggered by motion")
        return self._record_picture()

    def shutdown(self) -> None:
        """shutdown picam recording 
        """
        LOGGER.info(f"Shutting down")
        self._shutdown = True

    def _record_picture(self) -> List[str]:
        if self._shutdown:
            return []

        LOGGER.info("Recording pictures")

        date_str = date.today().strftime("%Y%m%d/")
        record_path = self._settings.record_path
        if not record_path.endswith("/"):
            record_path += "/"
        record_path += date_str

        recorded: List[str] = []
        for i in range(1, self._settings.record_count + 1):
            filename = self._settings.record_file_format.format(counter=i, timestamp=datetime.today())
            recorded.append(filename)

            LOGGER.info(f"Recorded picture to {record_path + filename}")
            if self._shutdown:
                LOGGER.debug("Record interrupted by shutdown")
                break

            time.sleep(self._settings.record_interval_sec)

        LOGGER.info("Finished recording")
        return recorded

    @property
    def id(self) -> int:
        return DummyCam._id
