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
        context = Context()
        data = []
        for device in context.list_devices(subsystem='block', DEVTYPE='partition'):
            properties = device.properties
            if ('ID_BUS' in properties and properties['ID_BUS'] == 'usb'
            and 'ID_FS_TYPE' in properties
            and 'ID_USB_DRIVER' in properties
            and properties['ID_USB_DRIVER'] == 'usb-storage'):
                data.append(True)
            else:
                data.append(False)
        if True in data:
            self.path = self.mount_device()
            if self.is_running:  # Double-check before emitting
                self.update_usb.emit(True, self.path)
        else:
            if self.is_running:  # Double-check before emitting
                self.update_usb.emit(False, "")

    def mount_device(self):
        context = Context()
        removable = [device for device in context.list_devices(subsystem='block', DEVTYPE='disk') if device.attributes.asstring('removable') == "1"]
        partition = []
        for device in removable:
            partitions = [device.device_node for device in device.parent.children if 'ID_FS_TYPE' in device.properties]
            if partitions:
                partition = partitions[0]
                result = subprocess.run(['findmnt', '-n', '-o', 'TARGET', partition], stdout=subprocess.PIPE, text=True)
                mount_point = result.stdout.strip()
                if mount_point:
                    return mount_point