#!/usr/bin/python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requires = f.read().splitlines()

setup(
    name='modulemd_tools',
    version='0.1',
    packages=find_packages(exclude=("tests",)),
    url='https://github.com/rpm-software-management/modulemd-tools',
    license='MIT',
    author='Jakub Kadlcik',
    author_email='frostyx@email.cz',
    description='Helper lib for working with modulemd YAML definitions',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # dir2module also requires libmodulemd and libdnf not available on PyPI
    # and must be installed separately.
    # On Fedora, this is done with `dnf install python3-libmodulemd python3-dnf`
    install_requires=requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    include_package_data=True,
)
