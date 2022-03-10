from modulemd_tools.modulemd_add_platform.modulemd_add_platform import process_string
import logging

logger = logging.getLogger('null')
logger.setLevel(logging.CRITICAL + 1)

modulemd_v2 = """
document: modulemd
version: 2
data:
    summary: text
    description: text
    license:
        module: [MIT]
    dependencies:
        - buildrequires:
            platform: []
          requires:
            platform: []
"""


def test_skip_modulemd_v2():
    error, output = process_string(logger, modulemd_v2, True, 'f35', 'f36')
    assert(error == -1)


def test_no_skip_modulemd_v2():
    error, output = process_string(logger, modulemd_v2, False, 'f35', 'f36')
    assert(error == 1)


missing_old_platform = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: 'A'
    """


def test_skip_without_old_platform():
    error, output = process_string(logger, missing_old_platform, True, 'B', 'B')
    assert(error == -1)


def test_no_skip_without_old_platform():
    error, output = process_string(logger, missing_old_platform, False, 'B', 'B')
    assert(error == 2)
