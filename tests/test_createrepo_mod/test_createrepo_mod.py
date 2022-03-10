import glob
import logging
import os.path
import shutil

import pytest

from modulemd_tools.createrepo_mod.createrepo_mod import (
    run_createrepo, run_modifyrepo, find_module_yamls, dump_modules_yaml)


logger = logging.getLogger(__name__)

dirname = os.path.dirname(os.path.realpath(__file__))
test_packages_dir = os.path.join(dirname, "packages")
test_module_yamls_dir = os.path.join(dirname, "module_yamls")
modulemd_merge = "/usr/bin/modulemd-merge"


def test_run_createrepo(test_output_dir):
    # I'd rather use shutil.copytree with dirs_exist_ok=True, but it requires Python 3.8+
    for package in glob.glob(os.path.join(test_packages_dir, "*.rpm")):
        shutil.copy(package, test_output_dir)
    retval = run_createrepo([test_output_dir])
    assert os.path.isdir(os.path.join(test_output_dir, "repodata"))
    assert os.path.isfile(os.path.join(test_output_dir, "repodata", "repomd.xml"))
    assert retval == 0


def test_find_module_yamls():
    assert len(find_module_yamls(test_module_yamls_dir)) > 0


# Ideally we would like to check if shutil.which("modulemd-merge") exists but
# it started failing in mock for some reason
@pytest.mark.skipif(not os.path.exists(modulemd_merge),
                    reason="requires modulemd-merge")
def test_dump_modules_yaml(test_output_dir):
    dump_modules_yaml(test_output_dir, find_module_yamls(test_module_yamls_dir))
    assert os.path.isfile(os.path.join(test_output_dir, "modules.yaml"))


def test_run_modifyrepo(test_output_dir):
    if not os.path.isfile(os.path.join(test_output_dir, "modules.yaml")):
        logger.info("Seems like test_dump_modules_yaml was skipped. "
                    "Creating modules.yaml from dummy.yaml.")
        shutil.copy(os.path.join(test_module_yamls_dir, "dummy.yaml"),
                    os.path.join(test_output_dir, "modules.yaml"))

    assert os.path.isfile(os.path.join(test_output_dir, "modules.yaml"))
    retval = run_modifyrepo(test_output_dir)
    assert glob.glob(os.path.join(test_output_dir, "repodata", "*-modules.yaml.gz"))
    assert retval == 0
