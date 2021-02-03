#!/usr/bin/python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requires = f.read().splitlines()

setup(
    name='createrepo_mod',
    version='0.1',
    packages=find_packages(),
    url='https://github.com/rpm-software-management/modulemd-tools',
    license='MIT',
    author='Jakub Kadlcik',
    author_email='frostyx@email.cz',
    description=('A small wrapper around `createrepo_c` and `modifyrepo_c` '
                 'to provide an easy tool for generating module repositories.'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    # createrepo_mod also requires libmodulemd not available on PyPI
    # and must be installed separately.
    # On Fedora, this is done with `dnf install python3-libmodulemd`
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'createrepo_mod=createrepo_mod.createrepo_mod:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    include_package_data=True,
)
