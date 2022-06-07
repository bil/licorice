from setuptools import setup

with open("install/requirements.in") as fh:
    # removes --no-binary and other options
    install_requires = [dep.split(" ")[0] for dep in fh.read().splitlines()]

with open("install/linux-requirements.in") as fh:
    # keeps platform-specific option
    install_requires += [dep for dep in fh.read().splitlines()]

setup(
    install_requires=install_requires,
)
