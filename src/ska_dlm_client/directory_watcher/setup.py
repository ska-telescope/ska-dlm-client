"""This is the setup code required for installing directory_watcher as an application."""

from setuptools import find_packages, setup

with open("../../.release", "r", encoding="utf-8") as vfile:
    for line in vfile.readlines():
        if "release" in line:
            version = line.split("../../../.release")[1].strip()[1:]
            break

setup(
    name="directory_watcher",
    version=version,
    description="The python package containing the python directory watcher",
    author="Mark Boulton",
    author_email="mark.boulton@uwa.edu.au",
    url="",
    license="",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    packages=find_packages(),
    include_package_data=True,
    package_data={"directory_watcher": ["README.md", "docs/*"]},
    # No spaces allowed between the '='s
    entry_points={
        "console_scripts": [
            "directory_watcher=ska_dlm_client.directory_watcher.directory_watcher:main",
        ],
    },
)
