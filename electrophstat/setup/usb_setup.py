from electrophstat.gui.usb_controller import UsbController


def init_usb(win):

    win.usb_monitor =  UsbController(win)

