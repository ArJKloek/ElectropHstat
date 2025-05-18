import csv
from pathlib import Path

import pytest

from electrophstat.io.logger import Logger

def test_logger_writes_into_tests_results(tmp_path):
    # 1) Point the base_dir at a clean tmp_path/results folder
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    # 2) Instantiate the Logger
    labels  = ["pH"]
    columns = ["pH"]
    logger = Logger(base_dir=results_dir, labels=labels, column_names=columns)

    # 3) The Logger tells us exactly the folder it created
    log_dir = logger.log_dir
    assert log_dir.exists() and log_dir.is_dir()
    # It should live under our results_dir
    assert log_dir.parents[1] == results_dir

    # 4) In that folder there must be exactly one CSV file for "pH"
    csv_files = list(log_dir.glob("pH_log_*.csv"))
    assert len(csv_files) == 1, f"Expected 1 CSV, found {csv_files}"
    csv_path = csv_files[0]

    # 5) That CSV should have exactly 4 rows: 3 pre‐header + header
    with open(csv_path, newline="", encoding="utf8") as f:
        rows = list(csv.reader(f, delimiter=";"))
    assert len(rows) == 4
    # confirm the column header is correct
    assert rows[3] == ["Reaction time (s)", "pH"]
