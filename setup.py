#!/usr/bin/python3
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='repo2module',
    version='0.1',
    packages=['repo2module'],
    url='https://github.com/sgallagher/repo2module',
    license='MIT',
    author='Stephen Gallagher',
    author_email='sgallagh@redhat.com',
    description='Tool to generate module metadata for a yum repo',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # repo2module also requires libmodulemd, libdnf and createrepo_c which are
    # not available on PyPI and must be installed separately. On Fedora, this
    # is done with
    # `dnf install python3-libmodulemd python3-createrepo_c python3-dnf`
    install_requires=[
        'click'
    ],
    entry_points={
        'console_scripts': [
            'repo2module=repo2module.cli:cli'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    include_package_data=True,
)
