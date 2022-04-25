import argparse
import os.path
from unittest.mock import patch

import pytest
import yaml

from modulemd_tools.modulemd_merge import modulemd_merge

dirname = os.path.dirname(os.path.realpath(__file__))
test_data_dir = os.path.join(dirname, "testdata")
test_repodata_dir = os.path.join(dirname, "testdata", "repodata")
test_repomd_file = os.path.join(dirname, "testdata", "repodata", "repomd.xml")


def _testrun_args(inputs, **kwargs):
    args = {'verbose': True, 'debug': True, 'input': inputs, 'to_stdout': True,
            'ignore_no_input': False}
    args.update(kwargs)
    return argparse.Namespace(**args)


def test_modulemd_merge_loading():
    assert modulemd_merge


def test_modulemd_merge_two_yamls(tmp_file, two_modules_merged_yamls):

    inputs = (os.path.join(test_data_dir, "moduleA.yaml"),
              os.path.join(test_data_dir, "moduleB.yaml"))
    kwargs = {"ignore_no_input": True, "output": tmp_file, "to_stdout": False}
    with patch("argparse.ArgumentParser.parse_args", return_value=_testrun_args(inputs, **kwargs)):
        modulemd_merge.main()

    with open(tmp_file, "r") as f:
        assert [d for d in yaml.load_all(f, Loader=yaml.SafeLoader)] == [
            d for d in yaml.load_all(two_modules_merged_yamls, Loader=yaml.SafeLoader)]


def test_modulemd_merge_two_yamls_first_missing():

    inputs = (os.path.join(test_data_dir, "missing-file.yaml"),
              os.path.join(test_data_dir, "moduleB.yaml"))
    with patch("argparse.ArgumentParser.parse_args", return_value=_testrun_args(inputs)):
        with pytest.raises(ValueError) as excinfo:
            modulemd_merge.main()

    assert f"input file {test_data_dir}/missing-file.yaml does not exist" in str(excinfo.value)


def test_modulemd_merge_two_yamls_first_missing_ignore_no_input(tmp_file, moduleB_yaml):

    inputs = (os.path.join(test_data_dir, "missing-file.yaml"),
              os.path.join(test_data_dir, "moduleB.yaml"))
    kwargs = {"ignore_no_input": True, "output": tmp_file, "to_stdout": False}
    with patch("argparse.ArgumentParser.parse_args", return_value=_testrun_args(inputs, **kwargs)):
        modulemd_merge.main()

    with open(tmp_file, "r") as f:
        assert [d for d in yaml.load_all(f, Loader=yaml.SafeLoader)] == [
            d for d in yaml.load_all(moduleB_yaml, Loader=yaml.SafeLoader)]


def test_modulemd_merge_module_with_repodata_dir(tmp_file, module_with_repodata_dir):

    inputs = (os.path.join(test_data_dir, "moduleA.yaml"),
              test_repodata_dir)
    kwargs = {"output": tmp_file, "to_stdout": False}
    with patch("argparse.ArgumentParser.parse_args", return_value=_testrun_args(inputs, **kwargs)):
        modulemd_merge.main()

    with open(tmp_file, "r") as f:
        assert [d for d in yaml.load_all(f, Loader=yaml.SafeLoader)] == [
            d for d in yaml.load_all(module_with_repodata_dir, Loader=yaml.SafeLoader)]


def test_modulemd_merge_module_with_repomd_file(tmp_file, module_with_repodata_dir):

    inputs = (os.path.join(test_data_dir, "moduleA.yaml"),
              test_repomd_file)
    kwargs = {"output": tmp_file, "to_stdout": False}
    with patch("argparse.ArgumentParser.parse_args", return_value=_testrun_args(inputs, **kwargs)):
        modulemd_merge.main()

    with open(tmp_file, "r") as f:
        assert [d for d in yaml.load_all(f, Loader=yaml.SafeLoader)] == [
            d for d in yaml.load_all(module_with_repodata_dir, Loader=yaml.SafeLoader)]
