from __future__ import annotations
import csv
import datetime
from pathlib import Path
from typing import Any, Dict, List

class Logger:
    """
    Generic CSV logger for arbitrary metrics.
    Fields are defined at initialization. Each `log()` call adds a row with timestamp and values.
    """
    def __init__(self, filepath: str, fields: List[str]) -> None:
        self.filepath = Path(filepath)
        self.fields = ["timestamp"] + fields
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.filepath.exists():
            with self.filepath.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.fields)
                writer.writeheader()

    def log(self, data: Dict[str, Any]) -> None:
        """Append a row to the CSV. `data` keys must match `fields`."""
        row = {"timestamp": datetime.datetime.utcnow().isoformat()}
        for field in self.fields[1:]:
            row[field] = data.get(field, "")
        with self.filepath.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fields)
            writer.writerow(row)

# Convenience factory

def create_logger(filepath: str, fields: List[str]) -> Logger:
    return Logger(filepath, fields)