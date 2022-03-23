import os
from unittest import mock
import tempfile

import pytest

from modulemd_tools.bld2repo import (
    get_buildrequire_pkgs_from_build, add_rpm_urls, rpm_bulk_download, create_repo)
from modulemd_tools.bld2repo.config import Config
from .utils import load_test_data


def test_get_buildrequire_pkgs_from_build_default():
    """ Test for gathering x86_64 build dependencies."""

    config = Config("koji_fake_url", "koji_fake_storage", "x86_64", ".")
    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    pkgs = get_buildrequire_pkgs_from_build("1234", mock_session, config)

    assert type(pkgs) == list
    assert len(pkgs) == 50
    for pkg in pkgs:
        for rpm in pkg["rpms"]:
            assert rpm["arch"] in ["x86_64", "noarch"]


def test_get_buildrequire_pkgs_from_build_aarch64():
    """ Test for gathering aarch64 build dependencies."""

    config = Config("koji_fake_url", "koji_fake_storage", "aarch64", ".")
    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    pkgs = get_buildrequire_pkgs_from_build("1234", mock_session, config)

    assert type(pkgs) == list
    assert len(pkgs) == 50
    for pkg in pkgs:
        for rpm in pkg["rpms"]:
            assert rpm["arch"] in ["aarch64", "noarch"]


def test_add_rpm_urls():
    """ Test for adding rpm urls to the pkgs dict for each package """

    config = Config("koji_fake_url", "koji_fake_storage", "x86_64", ".")
    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    pkgs = get_buildrequire_pkgs_from_build("1234", mock_session, config)
    pkgs, rpm_num = add_rpm_urls(pkgs, config)

    expected_rpm_num = 0
    for pkg in pkgs:
        assert len(pkg["rpms"]) == len(pkg["rpm_urls"])
        expected_rpm_num += len(pkg["rpms"])
        for rpm in pkg["rpms"]:
            rpm_filename = ("-".join([rpm["name"], rpm["version"], rpm["release"]]) +
                            "." + rpm["arch"])
            pkg_md = pkg["package"]
            expected_url = (config.koji_storage_host + "/vol/" + pkg_md["volume_name"] +
                            "/packages/" + pkg_md["package_name"] + "/" + pkg_md["version"] + "/" +
                            pkg_md["release"] + "/" + rpm["arch"] + "/" + rpm_filename + ".rpm")
            assert expected_url in pkg["rpm_urls"]

    assert expected_rpm_num == rpm_num


@mock.patch("modulemd_tools.bld2repo.download_file")
def test_rpm_bulk_download(mock_download_file):
    """ Test if the rpm files are downloaded. """

    tmp_dir = tempfile.TemporaryDirectory()
    config = Config("koji_fake_url", "koji_fake_storage", "x86_64", ".")

    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    def download_file(url, target_pkg_dir, filename):
        """ Mock function which fakes rpm downloads """
        abs_file_path = "/".join([target_pkg_dir, filename])
        open(abs_file_path, "w").close()

    mock_download_file.side_effect = download_file

    pkgs = get_buildrequire_pkgs_from_build("1234", mock_session, config)
    pkgs, rpm_num = add_rpm_urls(pkgs, config)
    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    # we gather all the files created on disk
    created_rpm_files = []
    for _, _, f in os.walk(tmp_dir.name):
        created_rpm_files += f

    # test if the number of created files is the same as provided by the metadata
    assert len(created_rpm_files) == rpm_num

    # test if the filenames are the same as described in the metadata
    for pkg in pkgs:
        for rpm_url in pkg["rpm_urls"]:
            rpm = rpm_url.split("/")[-1]
            assert rpm in created_rpm_files


@mock.patch("modulemd_tools.bld2repo.download_file")
def test_rpm_bulk_download_pkg_exist(mock_download_file):
    """ Test if we create each pkg dir only once. """

    tmp_dir = tempfile.TemporaryDirectory()
    config = Config("koji_fake_url", "koji_fake_storage", "x86_64", ".")

    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    def download_file(url, target_pkg_dir, filename):
        """ Mock function which fakes rpm downloads """
        abs_file_path = "/".join([target_pkg_dir, filename])
        open(abs_file_path, "w").close()

    mock_download_file.side_effect = download_file

    pkgs = get_buildrequire_pkgs_from_build("1234", mock_session, config)
    pkgs, rpm_num = add_rpm_urls(pkgs, config)
    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    with mock.patch("modulemd_tools.bld2repo.os.makedirs") as mock_makedirs:
        rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    assert not mock_makedirs.call_count


@mock.patch("modulemd_tools.bld2repo.download_file")
def test_rpm_bulk_download_rpm_file_exists(mock_download_file):
    """ Test if we download each rpm file only once. If the file exists we skip it. """

    tmp_dir = tempfile.TemporaryDirectory()
    config = Config("koji_fake_url", "koji_fake_storage", "x86_64", ".")

    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    def download_file(url, target_pkg_dir, filename):
        """ Mock function which fakes rpm downloads """
        abs_file_path = "/".join([target_pkg_dir, filename])
        open(abs_file_path, "w").close()

    mock_download_file.side_effect = download_file

    pkgs = get_buildrequire_pkgs_from_build("1234", mock_session, config)
    pkgs, rpm_num = add_rpm_urls(pkgs, config)
    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    # the call_count should be the same as the number of rpms in the metadata.
    # we called the rpm_bulk_download function twice, but the second time the download
    # part should be skipped for the same dir.
    assert mock_download_file.call_count == rpm_num


@mock.patch("modulemd_tools.bld2repo.download_file")
def test_create_repo(mock_download_file):
    """ Test to create a rpm repository of out a dir. """
    tmp_dir = tempfile.TemporaryDirectory()
    config = Config("koji_fake_url", "koji_fake_storage", "x86_64", ".")

    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    def download_file(url, target_pkg_dir, filename):
        """ Mock function which fakes rpm downloads """
        abs_file_path = "/".join([target_pkg_dir, filename])
        open(abs_file_path, "w").close()

    mock_download_file.side_effect = download_file

    pkgs = get_buildrequire_pkgs_from_build("1234", mock_session, config)
    pkgs, rpm_num = add_rpm_urls(pkgs, config)
    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)
    create_repo(tmp_dir.name)
    assert os.path.exists(tmp_dir.name + "/repodata")


def test_no_build_found_exception():
    """ Test raise when no build found """
    mock_session = mock.Mock()
    config = Config("koji_fake_url", "koji_fake_storage", "x86_64", ".")

    mock_session.getBuild.return_value = {}

    with pytest.raises(Exception) as ex:
        get_buildrequire_pkgs_from_build("1234", mock_session, config)

    err_msg = ex.value.args[0]
    assert "1234" in err_msg
    assert "not been found" in err_msg


def test_not_module_exception():
    """ Test raise when the build does not contain a build tag and is not a module. """
    mock_session = mock.Mock()
    config = Config("koji_fake_url", "koji_fake_storage", "x86_64", ".")

    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")

    mock_session.getBuild.return_value = build
    # we remove the build tag from the tags list
    tags.pop(1)
    mock_session.listTags.return_value = tags

    with pytest.raises(Exception) as ex:
        get_buildrequire_pkgs_from_build("1234", mock_session, config)

    err_msg = ex.value.args[0]
    assert "1234" in err_msg
    assert "not tagged" in err_msg
    assert "'build' tag" in err_msg
