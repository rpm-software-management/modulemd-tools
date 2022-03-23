import unittest
import os.path
import createrepo_c
import modulemd_tools.repo2module.cli
from modulemd_tools.repo2module.cli import parse_repodata, get_source_packages


dirname = os.path.dirname(os.path.realpath(__file__))
test_repo_dir = os.path.join(dirname, "rpmrepo")


def test_cli_module_loading():
    """Just a very simple/basic test that CLI module loading works."""
    assert modulemd_tools.repo2module.cli


def test_parse_repodata():
    packages = parse_repodata(test_repo_dir)
    assert len(packages) > 0
    assert all(isinstance(pkg, createrepo_c.Package) for pkg in packages)


def test_get_source_packages():
    packages = parse_repodata(test_repo_dir)
    source_packages = get_source_packages(packages)
    assert source_packages == {'python-django'}


@unittest.skip("Does not work with the latest libmodulemd (2.12.0)")
def test_repo2module(module_yaml_output):
    # runner = CliRunner()
    # result = runner.invoke(repo2module.cli.cli, ['-n', 'dummy', '-O', test_repo_dir])
    # assert result.exit_code == 0
    # assert result.output == module_yaml_output
    raise NotImplementedError
