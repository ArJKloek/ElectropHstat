# electrophstat/gui/usb_controller.py

from PyQt5.QtCore import QObject, QThread, pyqtSlot
from electrophstat.workers.usb_worker import USBWorker

class UsbController(QObject):
    """
    Manages background USB-insert/remove monitoring and
    enables/disables a USB button in the main window.
    """
    def __init__(self, win):
        super().__init__(win)
        self.win = win

        # 1) Prepare the worker
        self.worker = USBWorker()
        self.worker.is_running = True

        # 2) Move it into its own thread
        self.thread = QThread(self.win)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)

        # 3) Connect the signal to our slot
        #self.worker.update_usb.connect(self.on_usb_changed)

        # 4) Clean up when the window closes
        self.win.destroyed.connect(self.stop)

        # 5) Start monitoring
        self.thread.start()

    def stop(self):
        """Stop the worker thread cleanly."""
        self.worker.is_running = False
        self.thread.quit()
        self.thread.wait()
