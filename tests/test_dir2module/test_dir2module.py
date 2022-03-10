import unittest
import os.path

from modulemd_tools.dir2module.dir2module import (
    Module, Package, find_packages, parse_nsvca, parse_dependencies)


dirname = os.path.dirname(os.path.realpath(__file__))
test_packages_dir = os.path.join(dirname, "packages")


def test_dummy_module_loading(dummy_module):
    m = Module(**dummy_module)
    assert isinstance(m, Module)


def test_dummy_module_filename(dummy_module):
    m = Module(**dummy_module)
    assert m.filename == "dummy:0:1:2:noarch.modulemd.yaml"


@unittest.skip("Does not work with the latest libmodulemd (2.12.0)")
def test_dummy_module_dumps(dummy_module, dummy_module_mmd_as_string):
    m = Module(**dummy_module)
    output = m.dumps()
    assert output == dummy_module_mmd_as_string


def test_normal_package_loading():
    p = Package(os.path.join(test_packages_dir,
                             "python-django-bash-completion-3.0.10-3.fc33.noarch.rpm"))
    assert isinstance(p, Package)


def test_normal_package_license():
    p = Package(os.path.join(test_packages_dir,
                             "python-django-bash-completion-3.0.10-3.fc33.noarch.rpm"))
    assert p.license == "BSD"


def test_normal_package_has_not_modularity_label():
    p = Package(os.path.join(test_packages_dir,
                             "python-django-bash-completion-3.0.10-3.fc33.noarch.rpm"))
    assert p.has_modularity_label is False


def test_modular_package_has_modularity_label():
    p = Package(os.path.join(
        test_packages_dir,
        "python-django-bash-completion-1.6.11.8-1.module_f33+9570+f65235c8.noarch.rpm"))
    assert p.has_modularity_label is True


@unittest.skip("Does not work with the latest libmodulemd (2.12.0)")
def test_find_packages_in_directory():
    packages_files = [os.path.basename(rpm_abs_path)
                      for rpm_abs_path in find_packages(test_packages_dir)]
    assert packages_files == [
        'python-django-bash-completion-3.0.10-3.fc33.noarch.rpm',
        'python-django-bash-completion-1.6.11.8-1.module_f33+9570+f65235c8.noarch.rpm',
    ]


def test_parse_nsvca():
    assert parse_nsvca("dummy:0:1:2:noarch") == ['dummy', '0', 1, '2', 'noarch']


def test_parse_dependencies():
    assert parse_dependencies(['dummy:0']) == {'dummy': '0'}
