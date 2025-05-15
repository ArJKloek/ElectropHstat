import csv
import pytest
from pathlib import Path
from electrophstat.io.logger import Logger

def test_logger_creates_file_and_writes(tmp_path):
    fields = ["timestamp", "pH", "temperature", "volume"]
    log_file = tmp_path / "test_log.csv"
    logger = Logger(filepath=str(log_file), fieldnames=fields)
    logger.log({"timestamp": "2025-05-15T12:00:00", "pH": 7.1, "temperature": 25.0, "volume": 1.5})
    logger.log({"timestamp": "2025-05-15T12:01:00", "pH": 6.9, "temperature": 24.8, "volume": 2.0})

    with log_file.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        assert rows[0] == {'timestamp': '2025-05-15T12:00:00', 'pH': '7.1', 'temperature': '25.0', 'volume': '1.5'}
        assert rows[1] == {'timestamp': '2025-05-15T12:01:00', 'pH': '6.9', 'temperature': '24.8', 'volume': '2.0'}
