#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os.path

from setuptools import setup, find_packages

dirname = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dirname, "README.md")) as fh:
    long_description = fh.read()

with open(os.path.join(dirname, 'requirements.txt')) as f:
    requires = f.read().splitlines()

with open(os.path.join(dirname, 'test-requirements.txt')) as f:
    test_requires = f.read().splitlines()

setup(
    name='modulemd-tools',
    version='0.13',
    packages=find_packages(exclude=("tests",)),
    url='https://github.com/rpm-software-management/modulemd-tools',
    license='MIT',
    author='Jakub Kadlcik',
    author_email='jkadlcik@redhat.com',
    description=('Collection of tools for modular (in terms of Fedora Modularity'
                 'origin) content creators'),
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=requires,
    tests_require=test_requires,
    entry_points={
        'console_scripts': [
            'bld2repo=modulemd_tools.bld2repo.cli:main',
            'createrepo_mod=modulemd_tools.createrepo_mod.createrepo_mod:main',
            'dir2module=modulemd_tools.dir2module.dir2module:main',
            'modulemd-add-platform=modulemd_tools.modulemd_add_platform.modulemd_add_platform:main',
            'modulemd-generate-macros=modulemd_tools.modulemd_generate_macros.modulemd_generate_macros:main',
            'modulemd-merge=modulemd_tools.modulemd_merge.modulemd_merge:main',
            'repo2module=modulemd_tools.repo2module.cli:cli',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    include_package_data=True,
)

