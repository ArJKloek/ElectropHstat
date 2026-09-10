from electrophstat.workers.usb_worker import USBWorker


def test_usb_partition_detects_usb_by_bus_even_without_driver_metadata():
    worker = USBWorker()

    props = {
        "ID_BUS": "usb",
        "DEVTYPE": "partition",
    }

    assert worker._device_is_usb_storage(props) is True


def test_usb_partition_detects_filesystem_with_missing_driver_metadata():
    worker = USBWorker()

    props = {
        "ID_BUS": "sdio",
        "ID_FS_TYPE": "vfat",
    }

    assert worker._device_is_usb_storage(props) is True


def test_usb_partition_rejects_non_usb_device():
    worker = USBWorker()

    props = {
        "ID_BUS": "ata",
        "DEVTYPE": "partition",
    }

    assert worker._device_is_usb_storage(props) is False
