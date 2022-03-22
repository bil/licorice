from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("install/requirements.in") as fh:
    install_requires = [dep.split(" ")[0] for dep in fh.read().splitlines()]

setup(
    name="licorice",
    version="0.0.1",
    license="MIT,",
    description="Linux Comodular Realtime Interactive Compute Environment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Stanford Brain Interfacing Laboratory",
    author_email="licorice@bil.stanford.edu",
    install_requires=install_requires,
    packages=["licorice"],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "licorice_export_model = licorice.cli:export_model",
            "licorice_generate_model = licorice.cli:generate_model",
            "licorice_parse_model = licorice.cli:parse_model",
            "licorice_compile_model = licorice.cli:compile_model",
            "licorice_run_model = licorice.cli:run_model",
            "licorice_go = licorice.cli:go",
        ]
    },
)
