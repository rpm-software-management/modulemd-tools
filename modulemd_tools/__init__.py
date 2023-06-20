import sys

# There was changes in the project directory structure, see #53
# We want to ensure backward compatibility and allow users to import
# `modulemd_tools.yaml` as they did in the past because we consider the
# content of the `modulemd_tools/modulemd_tools` directory to be an API.
import modulemd_tools.modulemd_tools.yaml as yaml
sys.modules["modulemd_tools.yaml"] =\
    sys.modules["modulemd_tools.modulemd_tools.yaml"]
