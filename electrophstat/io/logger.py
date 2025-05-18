import csv
import os
import time
import locale
from datetime import datetime
from pathlib import Path

class Logger:
    """
    A CSV‐logger that:
      • Creates its own timestamped folder
      • Creates one CSV per “label” with pre-header + column header
      • Appends new data rows (reaction time + value) on demand
    """

    def __init__(self, base_dir: Path, labels: list, column_names: list):
        """
        base_dir: parent folder under which we’ll make Date/Time subfolders
        labels:    e.g. ["pH", "temperature", "volume"]
        column_names: e.g. ["pH", "°C", "mL"]
        """
        # 1) Set locale once
        try:
            locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')
        except locale.Error:
            pass  # fallback to default locale

        # 2) Create timestamped folder
        now = datetime.now()
        date_s = now.strftime("%d_%m_%Y")
        time_s = now.strftime("%H_%M_%S")
        self.log_dir = base_dir / date_s / time_s
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 3) For each label, create its CSV file
        self.files = {}      # label -> Path
        self.starts = {}     # label -> epoch when file was opened

        for lbl, col in zip(labels, column_names):
            p = self._make_file(lbl, col, now)
            self.files[lbl] = p
            self.starts[lbl] = time.time()

    def _make_file(self, label: str, column: str, now: datetime) -> Path:
        """
        Creates a single CSV:
          • pre-header lines:
             Label
             Date dd-mm-yyyy
             Start Time hh:mm:ss
          • then a semicolon-delimited header row:
             Reaction time (s);<column>
        Returns the Path to that new file.
        """
        fname = f"{label}_log_{now.strftime('%d%m%Y_%H%M%S')}.csv"
        p = self.log_dir / fname

        with open(p, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([label])
            writer.writerow([f"Date {now.strftime('%d-%m-%Y')}"])
            writer.writerow([f"Start Time {now.strftime('%H:%M:%S')}"])

            dict_w = csv.DictWriter(
                f,
                fieldnames=['Reaction time (s)', column],
                delimiter=';'
            )
            dict_w.writeheader()

        return p

    def log(self, label: str, value):
        """
        Append a new row for the given label:
          • Reaction time = seconds since file creation
          • value = formatted with locale grouping
        """
        if label not in self.files:
            raise KeyError(f"No such log label: {label}")

        path = self.files[label]
        start = self.starts[label]
        elapsed = time.time() - start

        # format numbers via locale
        if isinstance(value, (int, float)):
            val_s = locale.format_string("%.3f", value, grouping=True)
        else:
            val_s = str(value)

        time_s = locale.format_string("%.1f", elapsed, grouping=True)

        with open(path, 'a', newline='') as f:
            dict_w = csv.DictWriter(
                f,
                fieldnames=['Reaction time (s)', label],
                delimiter=';'
            )
            dict_w.writerow({
                'Reaction time (s)': time_s,
                label: val_s
            })

    def read(self, label: str):
        """
        Read back a given log file, returning (times, values) as floats.
        """
        p = self.files.get(label)
        if not p or not p.exists():
            return [], []

        with open(p, newline='') as f:
            reader = csv.reader(f, delimiter=';')
            # skip pre-header (3 lines) + header
            for _ in range(4):
                next(reader, None)

            times, vals = [], []
            for row in reader:
                if len(row) >= 2:
                    t = row[0].replace(',', '.')
                    v = row[1].replace(',', '.')
                    try:
                        times.append(float(t))
                        vals.append(float(v))
                    except ValueError:
                        continue
            return times, vals
