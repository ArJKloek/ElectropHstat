import csv
import time
import locale
from pathlib import Path

import pytest

# adjust this import if your Logger lives elsewhere
from electrophstat.io.logger import Logger

def test_logger_writes_multiple_files_into_repo_results(tmp_path, monkeypatch):
    # 1) Monkey‐patch time.time to simulate three 1s‐apart entries:
    #    First call in __init__ → 1000.0, then each .log() → +1s
    times = [1000.0, 1001.0, 1002.0, 1003.0, 1004.0, 1005.0, 1006.0, 1007.0]
    monkeypatch.setattr(time, "time", lambda: times.pop(0))
    # 2) No‐op locale so decimal = "."
    monkeypatch.setattr(locale, "setlocale", lambda *a, **k: None)

    # 3) Determine the tests/results folder in your repo root
    repo_root   = Path(__file__).parent # <repo>/tests
    results_dir = repo_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # 4) Instantiate Logger with two labels
    labels  = ["pH"]
    columns = ["pH"]
    logger = Logger(base_dir=results_dir, labels=labels, column_names=columns)

    # 5) After init, its log_dir should be <repo>/tests/results/<date>/<time>
    assert logger.log_dir.exists() and logger.log_dir.is_dir()
    assert results_dir in logger.log_dir.parents

    # 6) It should have created exactly two CSV files, one per label
    csv_files = sorted(logger.log_dir.glob("*_log_*.csv"))
    assert len(csv_files) == 1, f"Found CSVs: {csv_files}"
    # Map label→path
    files = { p.name.split("_log_")[0] : p for p in csv_files }
    assert set(files) == set(labels)

    # 7) Log three entries for each label
    logger.log("pH",  7.0)
    logger.log("pH",  7.1)
    logger.log("pH",  7.2)
    #logger.log("Temp", 25.0)
    #logger.log("Temp", 25.1)
    #logger.log("Temp", 25.2)

    # 8) Now read back each file and verify
    expected = [("1.0", "7.000"), ("2.0", "7.100"), ("3.0", "7.200")]
    for label, column in zip(labels, columns):
        path = files[label]
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f, delimiter=";"))

        # 3 pre‐header + 1 header + 3 data rows = 7 total
        assert len(rows) == 7, f"{label}: row count = {len(rows)}"
        # header row is row index 3
        assert rows[3] == ["Reaction time (s)", column]

        # check each data row
        for i, (ts, val) in enumerate(expected, start=4):
            got_ts, got_val = rows[i]
            assert got_ts  == ts,  f"{label} row{i} ts {got_ts!r} != {ts!r}"
            assert got_val == val, f"{label} row{i} val{got_val!r} != {val!r}"

    # 9) If you now look on disk under tests/results,
    #    you will see a dated folder with the two CSVs.
