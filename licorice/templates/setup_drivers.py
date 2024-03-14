import glob
import os
from distutils.core import Extension, setup

import numpy as np # TODO make configurable?
import yaml
from Cython.Build import cythonize

from licorice.utils import __find_in_path


def setup_drivers(package_name, module_name):
    driver_path = os.path.join(os.getcwd(), package_name)
    if not os.path.exists(driver_path):
        return

    driver_names = next(os.walk(driver_path))[1]
    driver_names = [name for name in driver_names if name != ""]

    if len(driver_names) == 0:
        return

    # dynamically add extra source files in driver folder
    driver_files = []
    driver_libs = []
    for name in driver_names:
        files = [f"{package_name}/{name}/{name}.pyx", "utilityFunctions.c"]
        files.extend(glob.glob(f"{package_name}/{name}/*.c"))
        driver_files.append(files)

        driver_conf_filepath = __find_in_path(
            [os.path.join(driver_path, name)],
            ["config.yaml", "config.yml"],
            raise_error=False,
        )
        libs = []
        if driver_conf_filepath:
            with open(driver_conf_filepath, "r") as f:
                try:
                    driver_conf = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML file with exception: {e}")
            if driver_conf.get("link_flags"):
                libs = [driver_conf["link_flags"][2:]]
        driver_libs.append(libs)

    driver_extension = [
        Extension(
            f"{package_name}.{module_name}",
            [f"{package_name}/{module_name}.pyx"],
            include_dirs=[os.getcwd()],
        )
    ]

    extensions = driver_extension + [
        Extension(
            f"{package_name}.{name}.{name}",
            files,
            include_dirs=[os.getcwd(), np.get_include()],
            libraries=libs,
        )
        for name, files, libs in zip(driver_names, driver_files, driver_libs)
    ]

    setup(
        name=package_name,
        ext_modules=cythonize(extensions, language_level=3),
    )


setup_drivers("source_drivers", "source_driver")
setup_drivers("sink_drivers", "sink_driver")
