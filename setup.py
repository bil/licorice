from setuptools import setup
from sys import platform
import re

with open("install/requirements.in") as fh:
    # removes --no-binary and other options
    install_requires = [
        re.sub(r"--.*", "", dep) for dep in fh.read().splitlines()
    ]

if "linux" in platform:
    with open("install/linux-requirements.in") as fh:
        # keeps platform-specific option
        install_requires += [dep for dep in fh.read().splitlines()]

setup(
    install_requires=install_requires,
)
