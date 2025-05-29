import csv
import time
import locale
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class Logger:
    """
    A CSV-logger that:
      • Stands ready until explicitly started
      • Creates its own timestamped folder (date/time) on start
      • Creates one CSV per "label" with pre-header + column header
      • Appends new data rows (reaction time + value) on demand
      • Can read back and reset logs
    """

    def __init__(
        self,
        base_dir: Path,
        labels: List[str],
        column_names: List[str]
    ):
        """
        base_dir: parent folder under which we’ll make date/time subfolders
        labels: list of log identifiers, e.g. ["pH", "RTD", "volume"]
        column_names: matching human-readable column names, e.g. ["pH", "°C", "mL"]
        """
        # store parameters
        self.base_dir = Path(base_dir)
        self.labels = labels.copy()
        self.columns = column_names.copy()

        # internal state
        self.log_dir: Optional[Path] = None
        self.files: Dict[str, Path] = {}
        self.starts: Dict[str, float] = {}


        # set locale for number formatting
        try:
            locale.setlocale(locale.LC_ALL, 'nl_NL.utf8')
        except locale.Error:
            pass  # fallback to system default

    def start_session(
        self,
        active_labels: Optional[List[str]] = None,
        initial_values: Optional[Dict[str, float]] = None
    ) -> None:
        now    = datetime.now()
        date_s = now.strftime("%d_%m_%Y")
        time_s = now.strftime("%H_%M_%S")
        self.log_dir = self.base_dir / date_s / time_s
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 1) choose which labels to enable
        labels_to_use = active_labels if active_labels is not None else self.labels

        # 2) clear any old session
        self.files.clear()
        self.starts.clear()

        # 3) create the files, mapping each label → its column name (and raw_data for turbidity)
        for lbl in labels_to_use:
            if lbl not in self.labels:
                continue
            idx   = self.labels.index(lbl)
            col   = self.columns[idx]
            if lbl == "turbidity":
                path = self._make_double_file(lbl, col, now)
            else:
                path = self._make_file(lbl, col, now)
            self.files[lbl]  = path
            self.starts[lbl] = time.monotonic()


        # 4) write out your zero-point rows (elapsed=0)
        if initial_values:
            for lbl, val in initial_values.items():
                if lbl not in self.files:
                    continue

                if lbl == "turbidity":
                    # Try to get both processed and raw values
                    proc = initial_values.get("turbidity", None)
                    raw = initial_values.get("turbidity_raw", None)
                    if proc is not None and raw is not None:
                        self._write_double_row(lbl, 0.0, proc, raw)
                    # else: skip writing if either is missing
                else:
                    self._write_row(lbl, 0.0, val)

    def reset(self) -> None:
        """
        Clear all session data without deleting files.
        Call start_session() to begin anew.
        """
        self.log_dir = None
        self.files.clear()
        self.starts.clear()

    def _make_file(
        self,
        label: str,
        column: str,
        now: datetime
    ) -> Path:
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
    
    def _make_double_file(
        self,
        label: str,
        column: str,
        now: datetime
    ) -> Path:
        """
        Special version for turbidity: adds a Raw Data column.
        """
        p = self.log_dir / f"{label}_log_{now.strftime('%d%m%Y_%H%M%S')}.csv"
        with open(p, 'w', newline='') as f:
            csv.writer(f, delimiter=';').writerow([label])
            csv.writer(f, delimiter=';').writerow([f"Date {now.strftime('%d-%m-%Y')}"])
            csv.writer(f, delimiter=';').writerow([f"Start Time {now.strftime('%H:%M:%S')}"])
            dict_w = csv.DictWriter(f,
                                    fieldnames=['Reaction time (s)', column, 'Raw Data'],
                                    delimiter=';')
            dict_w.writeheader()
        return p


    def log(
        self,
        label: str,
        value,
        elapsed: Optional[float] = None
    ) -> None:
        """
        Append a new row for the given label:
          • Reaction time = seconds since file creation
          • value = formatted via locale if numeric
        """
        if label not in self.files:
            raise KeyError(f"No such log label: {label}")
        if label not in self.starts:
            raise RuntimeError(f"Session not started for label: {label}")

        now = time.monotonic()
        start = self.starts[label]
        elapsed = elapsed if elapsed is not None else (now - start)

        ## format numbers via locale for grouping
        #if isinstance(value, (int, float)):
        #    val_s = locale.format_string("%.3f", value, grouping=True)
        #else:
        #    val_s = str(value)
        #time_s = locale.format_string("%.1f", elapsed, grouping=True)

        #self._write_row(label, elapsed, value)
                # for turbidity we expect a (processed, raw) tuple:
        if label == "turbidity" and isinstance(value, tuple):
            proc, raw = value
            self._write_double_row(label, elapsed, proc, raw)
        else:
            self._write_row(label, elapsed, value)

    def _write_row(
        self,
        label: str,
        elapsed: float,
        value
    ) -> None:
        
        """Internal: write a single row with given elapsed and value."""
        path = self.files[label]
        # format numbers
        if isinstance(value, (int, float)):
            val_s = locale.format_string("%.3f", value, grouping=False)
        else:
            val_s = str(value)
        time_s = locale.format_string("%.1f", elapsed, grouping=False)

        with open(path, 'a', newline='') as f:
            dict_w = csv.DictWriter(f, fieldnames=['Reaction time (s)', label], delimiter=';')
            dict_w.writerow({'Reaction time (s)': time_s, label: val_s})
    
    def _write_double_row(
        self,
        label: str,
        elapsed: float,
        processed,
        raw
    ) -> None:
        """Write a turbidity row with both processed and raw values."""
        path  = self.files[label]
        # format both numbers
        proc_s = locale.format_string("%.0f", processed, grouping=False) if isinstance(processed, (int,float)) else str(processed)
        raw_s  = locale.format_string("%.0f", raw, grouping=False)       if isinstance(raw, (int,float))       else str(raw)
        time_s = locale.format_string("%.1f", elapsed, grouping=False)

        with open(path, 'a', newline='') as f:
            dict_w = csv.DictWriter(f,
                                    fieldnames=['Reaction time (s)', label, 'Raw Data'],
                                    delimiter=';')
            dict_w.writerow({'Reaction time (s)': time_s,
                             label: proc_s,
                             'Raw Data': raw_s})
    def read(
        self,
        label: str
    ) -> Tuple[List[float], List[float]]:
        p = self.files.get(label)
        if not p or not p.exists():
            return [], []
        times: List[float] = []
        vals: List[float] = []
        with open(p, newline='') as f:
            reader = csv.reader(f, delimiter=';')
            for _ in range(4):
                next(reader, None)
 # if turbidity, pull out both data and raw_data
            if label == "turbidity":
                raw_vals: List[float] = []
                for row in reader:
                    if len(row) < 3:
                        continue
                    t_s   = row[0].replace(',', '.')
                    v_s   = row[1].replace(',', '.')
                    r_s   = row[2].replace(',', '.')
                    try:
                        times.append(float(t_s))
                        vals.append(float(v_s))
                        raw_vals.append(float(r_s))
                    except ValueError:
                        continue
                return times, vals, raw_vals
            else:
                for row in reader:
                    if len(row) < 2:
                        continue
                    t_s = row[0].replace(',', '.')
                    v_s = row[1].replace(',', '.')
                    try:
                        times.append(float(t_s))
                        vals.append(float(v_s))
                    except ValueError:
                        continue
                return times, vals, []            
