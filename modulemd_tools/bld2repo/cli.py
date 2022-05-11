import argparse

from modulemd_tools.bld2repo import (
    get_buildrequire_pkgs_from_build, add_rpm_urls, rpm_bulk_download, create_repo, filter_buildrequire_pkgs,
    get_koji_build_info)
from modulemd_tools.bld2repo.config import Config
from modulemd_tools.bld2repo.utils import get_koji_session


def get_arg_parser():
    description = (
        "When provided with a build id it will download all buildrequired RPMs"
        "of a modular koji build into the provided directory and create a repository out of it."
    )
    parser = argparse.ArgumentParser("bld2repo", description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-b", "--build-id", required=True, type=int, help="ID of a koji build.")
    parser.add_argument("-d", "--result-dir", help="Directory where the RPMs are downloaded.",
                        default=".", type=str)
    parser.add_argument("-a", "--arch", help=("For which architecture the RPMs should be download"
                                              "ed. The 'noarch' is included automatically."),
                        default="x86_64", type=str)
    parser.add_argument("-k", "--koji-host", type=str,
                        default="https://koji.fedoraproject.org/kojihub",
                        help="Koji host base url")
    parser.add_argument("-s", "--koji-storage-host", type=str,
                        default="https://kojipkgs.fedoraproject.org",
                        help=("Koji storage storage host base url. Server where the RPMs are "
                              "stored. Required to be used together with `--koji-host`."))
    parser.add_argument("-m", "--mbs-host", type=str,
                        default="https://mbs.fedoraproject.org",
                        help="Module Build Service host base url.")
    return parser


def main():
    parser = get_arg_parser()
    args = parser.parse_args()

    default_check = (
        args.koji_host == parser.get_default("koji_host"),
        args.koji_storage_host == parser.get_default("koji_storage_host"),
        args.mbs_host == parser.get_default("mbs_host")
    )

    if not all(default_check) and any(default_check):
        parser.error("--koji-host, --koji-storage-host and --mbs-host need to be used to together.")

    config = Config(args.koji_host, args.koji_storage_host,
                    args.mbs_host, args.arch, args.result_dir)

    session = get_koji_session(config)

    build = get_koji_build_info(args.build_id, session, config)

    pkgs = get_buildrequire_pkgs_from_build(build, session, config)

    pkgs = filter_buildrequire_pkgs(build, pkgs, config)

    pkgs, rpm_num = add_rpm_urls(pkgs, config)

    rpm_bulk_download(pkgs, rpm_num, config.result_dir)

    create_repo(config.result_dir)


if __name__ == "__main__":
    main()
