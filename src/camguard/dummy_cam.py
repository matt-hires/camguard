from datetime import date, datetime
import logging
import time
from typing import List
from .bridge import MotionHandlerImpl

LOGGER = logging.getLogger(__name__)


class DummyCam(MotionHandlerImpl):
    """dummy cam implementation
    this can be used for running camguard in a dummy mode
    """
    RECORD_FILE_FORMAT = "{counter:03d}_{timestamp:%y%m%d_%H%M%S}_{filename}.jpg"

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
        super().__init__()
        LOGGER.debug(f"Configuring dummy cam with params: "
                     f"record_root_path: {record_root_path}")
        self.record_root_path: str = record_root_path
        self.record_file_name: str = record_file_name
        self.record_interval_sec: float = record_interval_sec
        self.record_picture_count: int = record_count
        self._shutdown: bool = False

    def handle_motion(self) -> None:
        LOGGER.debug(f"Triggered by motion")
        recorded_pics = self._record_picture()

        if self.after_handling:
            self.after_handling(recorded_pics)

    def shutdown(self) -> None:
        """shutdown picam recording 
        """
        LOGGER.info(f"Shutting down")
        self._shutdown = True
        self.after_handling = None

    def _record_picture(self) -> List[str]:
        if self._shutdown:
            return

        LOGGER.info("Recording pictures")

        date_str = date.today().strftime("%Y%m%d/")
        if not self.record_root_path.endswith("/"):
            self.record_root_path += "/"

        record_path = self.record_root_path + date_str

        recorded = []
        for i in range(1, self.record_picture_count + 1):
            filename = self.RECORD_FILE_FORMAT.format(counter=i,
                                                      filename=self.record_file_name,
                                                      timestamp=datetime.today())
            recorded.append(filename)
            LOGGER.info(f"Recorded picture to {record_path + filename}")
            if self._shutdown:
                LOGGER.debug("Record interrupted by shutdown")
                break
            time.sleep(self.record_interval_sec)

        LOGGER.info("Finished recording")
        return recorded
