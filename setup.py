from setuptools import setup, find_packages

setup(
    name="electrophstat",
    version="0.1.0",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.7",
    install_requires=[
        "PyQt5",
        "pyserial",
        "smbus2",
        "typing_extensions; python_version < '3.8'",
    ],
    extras_require={
        "dev": ["pytest"],
    },
)
