from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("install/requirements.in") as fh:
    # removes --no-binary and other options
    install_requires = [dep.split(" ")[0] for dep in fh.read().splitlines()]

with open("install/linux-requirements.in") as fh:
    # keeps platform-specific option
    install_requires += [dep for dep in fh.read().splitlines()]

setup(
    name="bil-licorice",
    version="0.0.4",
    license="MIT,",
    description="Linux Comodular Realtime Interactive Compute Environment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Stanford Brain Interfacing Laboratory",
    author_email="licorice@bil.stanford.edu",
    install_requires=install_requires,
    packages=["licorice"],
    include_package_data=True,
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "licorice = licorice.cli:main",
        ]
    },
)
