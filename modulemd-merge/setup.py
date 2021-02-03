#!/usr/bin/python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requires = f.read().splitlines()

setup(
    name='modulemd-merge',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/rpm-software-management/modulemd-tools',
    license='MIT',
    author='Gerd v. Egidy',
    author_email='gerd.von.egidy@intra2net.com',
    description='Merge several modules.yaml files (rpm modularity metadata) into one',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # modulemd-merge also requires libmodulemd and createrepo_c which are
    # not available on PyPI and must be installed separately.
    # On Fedora, this is done with `dnf install python3-libmodulemd python3-createrepo_c`
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'modulemd-merge=modulemd_merge.modulemd_merge:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    include_package_data=True,
)
