#!/usr/bin/python3

"""
A small wrapper around `createrepo_c` and `modifyrepo_c` to provide an easy tool
for generating module repositories.

This is supposed to be only a temporary solution, in the future we would like to
have the modularity support implemented in `createrepo_c` itself. See

https://bugzilla.redhat.com/show_bug.cgi?id=1816753

Please see the official Fedora Modularity documentation for the reference of how
module repositories should be created

https://docs.fedoraproject.org/en-US/modularity/hosting-modules/
"""


import os
import sys
import subprocess
import argparse
from distutils.version import LooseVersion

import gi
gi.require_version("Modulemd", "2.0")
from gi.repository import Modulemd  # noqa: E402


def run_createrepo(args):
    cmd = ["createrepo_c"] + args
    proc = subprocess.run(cmd, check=True)
    return proc.returncode


def run_modifyrepo(path, compress_type=None):
    cmd = [
        "modifyrepo_c",
        "--mdtype", "modules",
        os.path.join(path, "modules.yaml"),
        os.path.join(path, "repodata"),
    ]

    if compress_type:
        cmd.extend(["--compress-type", compress_type])

    proc = subprocess.run(cmd, check=True)
    return proc.returncode


def find_module_yamls(path):
    """
    Recursivelly find modulemd YAML files and return a list of their relative
    paths.
    """
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if not filename.endswith((".yaml", ".yaml.gz")):
                continue
            filepath = os.path.join(root, filename)
            if not is_yaml_valid_modulemd(filepath):
                continue
            matches.append(filepath)
    return matches


def is_yaml_valid_modulemd(path):
    """
    Determine whether a YAML file is a valid modulemd file.
    If this simple check gets more and more complex, instead of adding
    logic here, consider calling `modulemd-validator` command, e.g.

        modulemd-validator -q foo.yaml

    """
    idx = Modulemd.ModuleIndex.new()
    (ret, _) = idx.update_from_file(path, strict=True)
    return ret


def dump_modules_yaml(path, yamls):
    """
    Go through all module YAMLs and merge them into one big YAML file.
    Then store the output as modules.yaml file in the `path` directory
    """
    cmd = ["modulemd-merge", "-i"]
    for yaml in yamls:
        cmd.append(yaml)
    cmd.append(os.path.join(path, "modules.yaml"))
    subprocess.run(cmd)


def createrepo_c_with_builtin_module_support():
    """
    There is a built-in support for module metadata in createrepo_c since
    version 0.16.1, please see the change log:
    rpm -q --changelog createrepo_c |less
    """
    cmd = ["rpm", "-q", "createrepo_c", "--queryformat", "%{VERSION}"]
    createrepo_c_version = subprocess.check_output(cmd).decode("utf-8")
    return LooseVersion(createrepo_c_version) >= LooseVersion("0.16.1")


def main():
    run_createrepo(sys.argv[1:])
    if createrepo_c_with_builtin_module_support():
        return

    parser = get_arg_parser()
    args, _ = parser.parse_known_args()
    yamls = find_module_yamls(args.path)
    if not yamls:
        return
    dump_modules_yaml(args.path, yamls)
    run_modifyrepo(args.path, "gz")


def get_arg_parser():
    # We are not going to define the whole parser here. Instead, we want to
    # pass all the input parameters to `createrepo_c` and let it handle them.
    #
    # We only need to define parser for a small subset of parameters that we
    # need to work within this script.

    description = ("A small wrapper around createrepo_c and modifyrepo_c to"
                   "provide an easy tool for generating module repositories")
    parser = argparse.ArgumentParser("createrepo_mod", description=description)
    parser.add_argument("path", metavar="directory_to_index",
                        help="Directory to index")
    return parser


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as ex:
        sys.stderr.write("Error: {0}\n".format(str(ex)))
        sys.exit(1)
