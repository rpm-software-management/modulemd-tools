#!/bin/bash
set -ex

SITEPACKAGES=true tox -vvv -e py310,flake8
rm -rf .tox/ build/ dist/ modulemd_tools.egg-info/
find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
