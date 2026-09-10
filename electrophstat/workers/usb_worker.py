from PyQt5.QtCore import QObject, pyqtSignal
import sys
import time
from serial.tools import list_ports

# On Linux we can use pyudev to watch for udev events; on Windows fall back
USE_PYUDEV = sys.platform.startswith("linux")
if USE_PYUDEV:
    from pyudev import Context, Monitor, MonitorObserver
else:
    Context = None
    Monitor = MonitorObserver = None

import subprocess

class USBWorker(QObject):
    update_usb = pyqtSignal(bool, object)

    def __init__(self):
        super().__init__()
        self.is_running = False  # Ensure this is always defined
        self.path = ""

    @staticmethod
    def _device_is_usb_storage(properties):
        if not properties:
            return False

        bus = str(properties.get("ID_BUS", "")).lower()
        id_path = str(properties.get("ID_PATH", "")).lower()
        driver = str(properties.get("ID_USB_DRIVER", "")).lower()
        fs_type = str(properties.get("ID_FS_TYPE", "")).lower()

        if bus == "usb" or "usb" in id_path or driver in {"usb-storage", "sd"}:
            return True

        # Some Raspberry Pi systems expose a mounted USB stick without the full
        # udev metadata. A valid filesystem on a block device is a strong enough
        # signal to treat it as USB storage for the copy button.
        return bool(fs_type)

    def run(self):
        self.is_running = True  # Set running flag when starting
        while self.is_running:
            self.monitor_usb()
            time.sleep(1)  # Adjust the sleep time as needed

    def stop(self):
        self.is_running = False

    def monitor_usb(self):
        if not self.is_running:
            return

        try:
            context = Context()
        except Exception:
            if self.is_running:
                self.update_usb.emit(False, "")
            return

        usb_present = False
        for device in context.list_devices(subsystem='block'):
            properties = device.properties
            if self._device_is_usb_storage(properties):
                usb_present = True
                break

        if usb_present:
            self.path = self.mount_device() or ""
            if self.is_running:
                self.update_usb.emit(True, self.path)
        else:
            self.path = ""
            if self.is_running:
                self.update_usb.emit(False, "")

    def mount_device(self):
        try:
            context = Context()
        except Exception:
            return ""

        removable = [
            device for device in context.list_devices(subsystem='block', DEVTYPE='disk')
            if self._device_is_usb_storage(device.properties)
        ]

        for device in removable:
            partition = None
            parent = getattr(device, 'parent', None)
            if parent is not None:
                for child in getattr(parent, 'children', []):
                    try:
                        if 'ID_FS_TYPE' in child.properties:
                            partition = child.device_node
                            break
                    except Exception:
                        continue

            if partition is None:
                partition = device.device_node

            result = subprocess.run(['findmnt', '-n', '-o', 'TARGET', partition], stdout=subprocess.PIPE, text=True)
            mount_point = result.stdout.strip()
            if mount_point:
                return mount_point

        return ""