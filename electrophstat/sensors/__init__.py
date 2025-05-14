from .dummy_atlas import DummyAtlas

def discover_ph_sensor(prefer_hw: bool = True):
    """
    Return a connected AtlasSensor instance.
    For now we always give DummyAtlas; later you’ll try I²C first.
    """
    # TODO: when the real driver exists, probe i2c bus here.
    sensor = DummyAtlas(kind="pH")
    sensor.connect()
    return sensor