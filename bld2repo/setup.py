#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path

from setuptools import setup, find_packages

dirname = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dirname, "README.md"), "r") as fh:
    long_description = fh.read()

with open(os.path.join(dirname, 'requirements.txt'), "r") as f:
    requires = f.read().splitlines()

setup(
    name='bld2repo',
    version='0.1',
    packages=find_packages(exclude=("tests",)),
    url='https://github.com/rpm-software-management/modulemd-tools',
    license='MIT',
    author='Martin Čurlej',
    author_email='mcurlej@redhat.com',
    description=('Tool to download modular build dependencies of '
                 'a modular build from koji.'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'bld2repo=bld2repo.cli:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    include_package_data=True,
)

