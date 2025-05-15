import csv


class Logger:
    """
    Generic CSV logger.
    On init it writes the header row; each .log() call appends one line.
    """

    def __init__(self, filepath: str, fieldnames: list):
        self.filepath = filepath
        self.fieldnames = fieldnames

        # (Re)create the CSV file with header
        with open(self.filepath, mode="w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()

    def log(self, data: dict):
        """
        Append one row to the CSV. All values are cast to str.
        Expects keys in data to match fieldnames.
        """
        with open(self.filepath, mode="a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writerow({k: str(v) for k, v in data.items()})
