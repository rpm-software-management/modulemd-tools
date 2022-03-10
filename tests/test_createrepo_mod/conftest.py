import pytest


@pytest.fixture(scope="session")
def test_output_dir(tmpdir_factory):
    test_output_dir = tmpdir_factory.mktemp("output")
    return test_output_dir
