from setuptools import setup, find_packages

setup(
    name="electrophstat",
    version="0.1.0",
    author="Arjan Kloekhorst",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.7",
    install_requires=[
        "PyQt5",
        "pyqtgraph",         # For plotting
        "pyserial",          # For serial communication
        "smbus2",            # For I2C communication
        "numpy",             # Used in calibration/modeling
        "scipy",             # Used in model fitting
        "typing_extensions; python_version < '3.8'",
    ],
    extras_require={
        "dev": ["pytest"],
    },
)
