# scripts/pHStat_worker.py
import sys
import time
import subprocess
from PyQt5.QtCore import QObject, pyqtSignal

# Linux only
USE_PYUDEV = sys.platform.startswith("linux")
if USE_PYUDEV:
    from pyudev import Context, Monitor, MonitorObserver

# Windows only
USE_PSUTIL = sys.platform.startswith(("win32", "cygwin"))
if USE_PSUTIL:
    import psutil
    from ctypes import windll

    def _is_removable(drive: str) -> bool:
        # drive like "D:\\"
        DRIVE_REMOVABLE = 2
        dtype = windll.kernel32.GetDriveTypeW(drive)
        return dtype == DRIVE_REMOVABLE


class USBWorker(QObject):
    """
    Emits update_usb(connected: bool, path: str) whenever a removable
    storage device appears/disappears.
    """
    update_usb = pyqtSignal(bool, str)

    def __init__(self, interval: float = 1.0):
        super().__init__()
        self.interval = interval
        self.is_running = True

        if USE_PYUDEV:
            # Setup udev monitor
            self._ctx      = Context()
            self._monitor  = Monitor.from_netlink(self._ctx)
            self._observer = MonitorObserver(self._monitor, callback=self._on_event)
            self._observer.start()
        else:
            # Polling fallback: track existing mount points
            self._known = set(self._list_current())

    def run(self):
        while self.is_running:
            if not USE_PYUDEV:
                self._poll_windows_linux()
            time.sleep(self.interval)

    def stop(self):
        self.is_running = False
        if USE_PYUDEV:
            self._observer.stop()

    # ─── Linux udev callback ─────────────────────────────────────────
    def _on_event(self, action, device):
        # Only care about block partitions
        if device.subsystem != "block" or device.device_type != "partition":
            return
        props = device.properties
        if props.get("ID_BUS") != "usb" or props.get("ID_FS_TYPE") is None:
            return

        node = device.device_node  # e.g. "/dev/sda1"
        if action == "add":
            mount = self._find_mount_linux(node)
            self.update_usb.emit(True, mount or node)
        elif action == "remove":
            self.update_usb.emit(False, node)

    def _find_mount_linux(self, partition: str) -> str:
        # findmnt -n -o TARGET /dev/sda1
        try:
            res = subprocess.run(
                ["findmnt", "-n", "-o", "TARGET", partition],
                stdout=subprocess.PIPE,
                text=True,
                check=True
            )
            return res.stdout.strip()
        except subprocess.CalledProcessError:
            return partition

    # ─── Polling for Windows & fallback Linux ─────────────────────────
    def _listen_devices(self):
        if USE_PSUTIL:
            # Windows: list all partitions like 'D:\\'
            return [p.device for p in psutil.disk_partitions(all=False)]
        else:
            # Linux fallback: list mounted block devices
            # e.g. parse /proc/mounts or reuse findmnt
            return [
                line.split()[1]
                for line in subprocess.check_output(["lsblk", "-ln", "-o", "MOUNTPOINT"]).splitlines()
                if line.strip()
            ]

    def _poll_windows_linux(self):
        current = set(self._listen_devices())
        added   = current - self._known
        removed = self._known - current

        # New mounts
        for p in added:
            if USE_PSUTIL:
                if _is_removable(p):
                    self.update_usb.emit(True, p)
            else:
                # on Linux fallback, assume all are USB for this path
                self.update_usb.emit(True, p)

        # Removed mounts
        for p in removed:
            self.update_usb.emit(False, p)

        self._known = current
