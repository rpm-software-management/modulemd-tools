#!/usr/bin/python3
#
# merge several modules.yaml files (rpm modularity metadata) into one
#
# Copyright (c) 2020 Gerd v. Egidy
# License: MIT
# https://github.com/rpm-software-management/modulemd-tools
#

import os
import sys
import logging
import argparse

import createrepo_c as cr

import gi
gi.require_version("Modulemd", "2.0")
from gi.repository import Modulemd  # noqa: E402


def hande_repomd(args, merger, repomd_filename):
    try:
        repomd = cr.Repomd(repomd_filename)
    except (RuntimeError, ValueError) as err:
        if not args.ignore_no_input:
            raise err
        logging.debug("{}: error loading repomd.xml: {}".format(repomd_filename, str(err)))
        return False

    # repomd was loaded and decoded successfully
    modules_path = False
    for record in repomd.records:
        if record.type == "modules":
            modules_path = record.location_href

    if not modules_path:
        logging.debug("{fn}: no modules section found in repomd.xml".format(fn=repomd_filename))
        if not args.ignore_no_input:
            raise ValueError('{fn} does not contain a modules section'.format(fn=repomd_filename))
        return False

    # strip repodata-prefix-dir from location_href
    filename = os.path.join(os.path.dirname(repomd_filename), os.path.basename(modules_path))
    if os.path.isfile(filename):
        return merge_file(merger, filename)

    filename = os.path.join(os.path.dirname(repomd_filename), "../", modules_path)
    if os.path.isfile(filename):
        return merge_file(merger, filename)

    logging.debug("{fn}: modules section found in repomd.xml, but href file {href} does not exist".
                  format(fn=repomd_filename, href=filename))
    if not args.ignore_no_input:
        raise ValueError("{fn}: modules section found in repomd.xml, but href file {href} does "
                         "not exist".format(fn=repomd_filename, href=filename))
    return False


# check type and existence of input file, directly or indirectly calls merge_file
# when a yaml is found
def merge_input(args, merger, filename):
    if os.path.isdir(filename):
        logging.debug("{}: is a directory".format(filename))
        if os.path.isfile(os.path.join(filename, "repodata/repomd.xml")):
            hande_repomd(args, merger, os.path.join(filename, "repodata/repomd.xml"))
        elif os.path.isfile(os.path.join(filename, "repomd.xml")):
            hande_repomd(args, merger, os.path.join(filename, "repomd.xml"))
        else:
            logging.debug("{}: no repomd.xml in or below directory".format(filename))
            if not args.ignore_no_input:
                raise ValueError('{fn} is a directory, but no repomd.xml file existing in or below'
                                 .format(fn=filename))

    elif os.path.isfile(filename):
        logging.debug("{}: is a regular file".format(filename))

        if os.path.basename(filename) == "repomd.xml":
            hande_repomd(args, merger, filename)
        else:
            merge_file(merger, filename)

    else:
        logging.debug("{}: file does not exist".format(filename))
        if not args.ignore_no_input:
            raise ValueError('input file {fn} does not exist'.format(fn=filename))


def merge_file(merger, filename):
    logging.debug("{}: Loading YAML".format(filename))

    index = Modulemd.ModuleIndex.new()
    ret, failures = index.update_from_file(filename, True)
    if not ret:
        failmsglst = []
        for err in failures:
            failmsglst.append(err.get_gerror().message)
        raise ValueError('Error parsing {fn}'.format(fn=filename), failmsglst)

    modnames = index.get_module_names()
    defstreams = index.get_default_streams()
    logging.info("{}: Found {} modulemds and {} modulemd-defaults".format(filename, len(modnames),
                 len(defstreams)))

    merger.associate_index(index, 0)


def get_arg_parser():
    description = "Merge several modules.yaml files (rpm modularity metadata) into one."
    parser = argparse.ArgumentParser("modulemd-merge", description=description,
                                     formatter_class=argparse.RawTextHelpFormatter)

    # flag options
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    parser.add_argument("-d", "--debug", help="debug output verbosity",
                        action="store_true")
    parser.add_argument("-i", "--ignore-no-input", help="ignore non-existing input files",
                        action="store_true")
    parser.add_argument("-O", "--to-stdout", help="print YAML output to stdout",
                        action="store_true")

    # positional arguments
    parser.add_argument("input", nargs="+", help="input filename(s) or directories.\n"
                        "repomd.xml files are parsed and modules hrefs contained are merged.\n"
                        "If a directory is given, it is searched for repodata/repomd.xml\n"
                        "and repomd.xml")
    parser.add_argument("output", help="YAML output filename")
    return parser


def parse_args():
    parser = get_arg_parser()
    args = parser.parse_args()

    if args.verbose and not args.debug:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
    if args.debug:
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    return args


def main():
    args = parse_args()

    merger = Modulemd.ModuleIndexMerger.new()

    for i in args.input:
        merge_input(args, merger, i)

    merged_index = merger.resolve()

    modnames = merged_index.get_module_names()
    defstreams = merged_index.get_default_streams()
    logging.info("merged result: {} modulemds and {} modulemd-defaults".format(len(modnames),
                                                                               len(defstreams)))

    if args.to_stdout:
        output = sys.stdout
    else:
        logging.debug("Writing YAML to {}".format(args.output))
        output = open(args.output, 'w')

    if len(modnames) == 0 and len(defstreams) == 0:
        # properly writing a completely empty yaml document
        logging.debug("Writing an empty YAML")
        output.write("")
    else:
        output.write(merged_index.dump_to_string())

    if not args.to_stdout:
        output.close()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as ex:
        sys.stderr.write("Error: {0}\n".format(str(ex)))
        sys.exit(1)
