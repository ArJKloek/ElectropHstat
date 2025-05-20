import csv
import time
import locale
from datetime import datetime
from pathlib import Path

class Logger:
    """
    A CSV-logger that:
      • Stands ready until explicitly started
      • Creates its own timestamped folder (date/time) on start
      • Creates one CSV per "label" with pre-header + column header
      • Appends new data rows (reaction time + value) on demand
      • Can read back and reset logs
    """

    def __init__(self, base_dir: Path, labels: list[str], column_names: list[str]):
        """
        base_dir: parent folder under which we’ll make date/time subfolders
        labels: list of log identifiers, e.g. ["pH", "temperature", "volume"]
        column_names: matching human-readable column names, e.g. ["pH", "°C", "mL"]
        """
        # store parameters
        self.base_dir = Path(base_dir)
        self.labels = labels.copy()
        self.columns = column_names.copy()

        # prepare internal state
        self.log_dir: Path | None = None
        self.files: dict[str, Path] = {}
        self.starts: dict[str, float] = {}

        # set locale for number formatting
        try:
            locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')
        except locale.Error:
            pass  # fallback to system default

    def start_session(self) -> None:
        """
        Initialize a new logging session:
          • create date/time directories
          • create one CSV file per label with pre-headers and headers
        """
        now = datetime.now()
        date_s = now.strftime("%d_%m_%Y")
        time_s = now.strftime("%H_%M_%S")
        self.log_dir = self.base_dir / date_s / time_s
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # clear previous session state
        self.files.clear()
        self.starts.clear()

        # create files for each label
        for lbl, col in zip(self.labels, self.columns):
            path = self._make_file(lbl, col, now)
            self.files[lbl] = path
            self.starts[lbl] = time.monotonic()

    def reset(self) -> None:
        """
        Clear all session data without deleting files.
        Call start_session() to begin anew.
        """
        self.log_dir = None
        self.files.clear()
        self.starts.clear()

    def _make_file(self, label: str, column: str, now: datetime) -> Path:
        """
        Creates a single CSV with:
            Label pre-header line
            Date dd-mm-yyyy line
            Start Time hh:mm:ss line
            header row: Reaction time (s);<column>
        Returns the Path to that new file.
        """
        if self.log_dir is None:
            raise RuntimeError("Logging session not started. Call start_session() first.")

        fname = f"{label}_log_{now.strftime('%d%m%Y_%H%M%S')}.csv"
        p = self.log_dir / fname
        with open(p, 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([label])
            writer.writerow([f"Date {now.strftime('%d-%m-%Y')}"])
            writer.writerow([f"Start Time {now.strftime('%H:%M:%S')}"])
            dict_w = csv.DictWriter(f, fieldnames=['Reaction time (s)', column], delimiter=';')
            dict_w.writeheader()
        return p

    def log(self, label: str, value) -> None:
        """
        Append a new row for the given label:
          • Reaction time = seconds since file creation
          • value = formatted via locale if numeric
        """
        if label not in self.files:
            raise KeyError(f"No such log label: {label}")

        path = self.files[label]
        start = self.starts[label]
        elapsed = time.monotonic() - start

        # format numbers via locale for grouping
        if isinstance(value, (int, float)):
            val_s = locale.format_string("%.3f", value, grouping=True)
        else:
            val_s = str(value)
        time_s = locale.format_string("%.1f", elapsed, grouping=True)

        with open(path, 'a', newline='') as f:
            dict_w = csv.DictWriter(f, fieldnames=['Reaction time (s)', label], delimiter=';')
            dict_w.writerow({'Reaction time (s)': time_s, label: val_s})

    def read(self, label: str) -> tuple[list[float], list[float]]:
        """
        Read back a given log file, returning two lists of floats:
        (reaction_times_s, values).
        """
        p = self.files.get(label)
        if not p or not p.exists():
            return [], []

        times: list[float] = []
        vals: list[float] = []
        with open(p, newline='') as f:
            reader = csv.reader(f, delimiter=';')
            # skip 3 pre-header lines + header
            for _ in range(4):
                next(reader, None)
            for row in reader:
                if len(row) < 2:
                    continue
                t_s, v_s = row[0], row[1]
                # normalize decimal mark
                t_s = t_s.replace(',', '.')
                v_s = v_s.replace(',', '.')
                try:
                    times.append(float(t_s))
                    vals.append(float(v_s))
                except ValueError:
                    continue
        return times, vals
