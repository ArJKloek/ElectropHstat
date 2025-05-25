from electrophstat.gui.usb_controller import UsbController


def init_usb(win):

    win.statusBar().installEventFilter(win)
    win.usb_ctrl =  UsbController(win)

def eventFilter(self, obj, evt):
    if obj is self.statusBar() and evt.type() == QEvent.StatusTip:
            # swallow status-tip events so they don't override our message
        return True
    return super().eventFilter(obj, evt)


