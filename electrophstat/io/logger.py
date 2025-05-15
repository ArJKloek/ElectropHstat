# electrophstat/io/logger.py
import csv
from pathlib import Path

class Logger:
    """
    Handles CSV logging of time-series data.
    """
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self._file = open(self.filepath, mode='a', newline='')
        self._writer = csv.writer(self._file)
        # write header if file is new
        if self._file.tell() == 0:
            self._writer.writerow(["timestamp", "pH", "temp", "... etc ..."])

    def log(self, **data) -> None:
        """Append a row: timestamp + named fields"""
        row = [data.get("timestamp"), data.get("pH"), data.get("temp")]
        self._writer.writerow(row)
        self._file.flush()

    def close(self) -> None:
        self._file.close()