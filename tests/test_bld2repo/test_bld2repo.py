import os
from unittest import mock
import tempfile
import json
import pytest

from modulemd_tools.bld2repo import (
    filter_buildrequire_pkgs, get_buildrequire_pkgs_from_build, add_rpm_urls, rpm_bulk_download, create_repo, get_koji_build_info)
from modulemd_tools.bld2repo.config import Config


def test_get_buildrequire_pkgs_from_build_default(load_test_data):
    """ Test for gathering x86_64 build dependencies."""

    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "x86_64", ".")
    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    build = get_koji_build_info("1234", mock_session, config)
    pkgs = get_buildrequire_pkgs_from_build(build, mock_session, config)

    assert type(pkgs) == list
    assert len(pkgs) == 50
    for pkg in pkgs:
        for rpm in pkg["rpms"]:
            assert rpm["arch"] in ["x86_64", "noarch"]


def test_get_buildrequire_pkgs_from_build_aarch64(load_test_data):
    """ Test for gathering aarch64 build dependencies."""

    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "aarch64", ".")
    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    build = get_koji_build_info("1234", mock_session, config)
    pkgs = get_buildrequire_pkgs_from_build(build, mock_session, config)

    assert type(pkgs) == list
    assert len(pkgs) == 50
    for pkg in pkgs:
        for rpm in pkg["rpms"]:
            assert rpm["arch"] in ["aarch64", "noarch"]


@mock.patch("modulemd_tools.bld2repo.download_file")
@pytest.mark.parametrize("arch", ["aarch64", "x86_64"])
@pytest.mark.parametrize("wrong_mbs_build_id", [False, "missing", "bad"])
@pytest.mark.parametrize("missing_modulemd", [True, False])
def test_filter_buildrequire_pkgs(mock_download_file, arch, wrong_mbs_build_id, missing_modulemd, load_test_data):
    """ Test for filtering build dependencies based on builorder."""

    # This have conflict exceptions. No need to test it.
    if wrong_mbs_build_id and missing_modulemd:
        pytest.skip("Conflicting exceptions. Test not needed.")

    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", arch, ".")
    build = load_test_data("librevenge_build")
    tags = load_test_data("librevenge_tags")
    build_tag_md = load_test_data("librevenge_build_tag")
    mbs_build_data = load_test_data("librevenge_mbs_build")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    if missing_modulemd:
        del mbs_build_data["modulemd"]

    mock_download_file.return_value = json.dumps(mbs_build_data)

    build = get_koji_build_info("1234", mock_session, config)
    pkgs = get_buildrequire_pkgs_from_build(build, mock_session, config)

    # Fake wrong mbs build_id
    if wrong_mbs_build_id == "missing":
        build['release'] = build['release'].replace("+", ".")
    elif wrong_mbs_build_id == "bad":
        char_idx = build['release'].rfind("+")
        build['release'] = build['release'][:char_idx] + "d+" + build['release'][char_idx + 2:]

    if missing_modulemd:
        with pytest.raises(Exception, match="Metadata modulemd not found"):
            filter_buildrequire_pkgs(build, pkgs, config)
    elif wrong_mbs_build_id:
        match_error_msg = "cannot be found" if wrong_mbs_build_id == "missing" else "is not valid"
        with pytest.raises(Exception, match=match_error_msg):
            filter_buildrequire_pkgs(build, pkgs, config)
    else:
        pkgs_filtered = filter_buildrequire_pkgs(build, pkgs, config)

        assert type(pkgs) == list
        assert len(pkgs) == 197
        assert len(pkgs_filtered) == 3
        for pkg in pkgs_filtered:
            for rpm in pkg["rpms"]:
                assert rpm["arch"] in [arch, "noarch"]


def test_add_rpm_urls(load_test_data):
    """ Test for adding rpm urls to the pkgs dict for each package """

    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "x86_64", ".")
    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")
    build_tag_md = load_test_data("pki_core_build_tag")

    mock_session = mock.Mock()

    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags
    mock_session.listTaggedRPMS.return_value = build_tag_md

    build = get_koji_build_info("1234", mock_session, config)
    pkgs = get_buildrequire_pkgs_from_build(build, mock_session, config)
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
def test_rpm_bulk_download(mock_download_file, load_test_data):
    """ Test if the rpm files are downloaded. """

    tmp_dir = tempfile.TemporaryDirectory()
    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "x86_64", ".")

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

    build = get_koji_build_info("1234", mock_session, config)
    pkgs = get_buildrequire_pkgs_from_build(build, mock_session, config)
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
def test_rpm_bulk_download_pkg_exist(mock_download_file, load_test_data):
    """ Test if we create each pkg dir only once. """

    tmp_dir = tempfile.TemporaryDirectory()
    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "x86_64", ".")

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

    build = get_koji_build_info("1234", mock_session, config)
    pkgs = get_buildrequire_pkgs_from_build(build, mock_session, config)
    pkgs, rpm_num = add_rpm_urls(pkgs, config)
    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    with mock.patch("modulemd_tools.bld2repo.os.makedirs") as mock_makedirs:
        rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    assert not mock_makedirs.call_count


@mock.patch("modulemd_tools.bld2repo.download_file")
def test_rpm_bulk_download_rpm_file_exists(mock_download_file, load_test_data):
    """ Test if we download each rpm file only once. If the file exists we skip it. """

    tmp_dir = tempfile.TemporaryDirectory()
    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "x86_64", ".")

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

    build = get_koji_build_info("1234", mock_session, config)
    pkgs = get_buildrequire_pkgs_from_build(build, mock_session, config)
    pkgs, rpm_num = add_rpm_urls(pkgs, config)
    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)

    # the call_count should be the same as the number of rpms in the metadata.
    # we called the rpm_bulk_download function twice, but the second time the download
    # part should be skipped for the same dir.
    assert mock_download_file.call_count == rpm_num


@mock.patch("modulemd_tools.bld2repo.download_file")
def test_create_repo(mock_download_file, load_test_data):
    """ Test to create a rpm repository of out a dir. """
    tmp_dir = tempfile.TemporaryDirectory()
    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "x86_64", ".")

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

    build = get_koji_build_info("1234", mock_session, config)
    pkgs = get_buildrequire_pkgs_from_build(build, mock_session, config)
    pkgs, rpm_num = add_rpm_urls(pkgs, config)
    rpm_bulk_download(pkgs, rpm_num, tmp_dir.name)
    create_repo(tmp_dir.name)
    assert os.path.exists(tmp_dir.name + "/repodata")


def test_no_build_found_exception():
    """ Test raise when no build found """
    mock_session = mock.Mock()
    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "x86_64", ".")

    mock_session.getBuild.return_value = {}

    with pytest.raises(Exception) as ex:
        get_koji_build_info("1234", mock_session, config)

    err_msg = ex.value.args[0]
    assert "1234" in err_msg
    assert "not been found" in err_msg


def test_not_module_exception(load_test_data):
    """ Test raise when the build does not contain a build tag and is not a module. """
    mock_session = mock.Mock()
    config = Config("koji_fake_url", "koji_fake_storage", "mbs_fake_storage", "x86_64", ".")

    build = load_test_data("pki_core_build")
    tags = load_test_data("pki_core_tags")

    # we remove the build tag from the tags list
    tags.pop(1)
    mock_session.getBuild.return_value = build
    mock_session.listTags.return_value = tags

    build = get_koji_build_info("1234", mock_session, config)

    with pytest.raises(Exception) as ex:
        get_buildrequire_pkgs_from_build(build, mock_session, config)

    err_msg = ex.value.args[0]
    assert "1557161" in err_msg
    assert "not tagged" in err_msg
    assert "'build' tag" in err_msg
