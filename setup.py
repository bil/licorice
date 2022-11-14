import re

from setuptools import setup

with open("install/requirements.in") as fh:
    # removes --no-binary and other options
    install_requires = [
        re.sub(r"--.*", "", dep) for dep in fh.read().splitlines()
    ]

setup(
    install_requires=install_requires,
)
