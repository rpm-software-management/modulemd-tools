import pytest
from modulemd_add_platform.modulemd_add_platform \
        import process_string, dequote_yaml_string
import logging

logger = logging.getLogger('null')
logger.setLevel(logging.CRITICAL + 1)

def test_no_quotes():
    """Original uses no quotes, output has them too.
    """

    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: A
          platform: A
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: A
          platform: A
        - context: B
          platform: B
    """

    error, output = process_string(logger, input, 'A', 'B')
    assert(error == 0)
    assert(output == expected)

def test_single_quotes():
    """Original uses single quotes, output has them too.
    """

    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: 'A'
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: 'A'
        - context: 'B'
          platform: 'B'
    """

    error, output = process_string(logger, input, 'A', 'B')
    assert(error == 0)
    assert(output == expected)

def test_double_quotes():
    """Original uses double quotes, output has them too.
    """

    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: "A"
          platform: "A"
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: "A"
          platform: "A"
        - context: "B"
          platform: "B"
    """

    error, output = process_string(logger, input, 'A', 'B')
    assert(error == 0)
    assert(output == expected)

def test_single_quoted_escaping():
    """Sinlge quotes recongizes only a doubled single quote.
    """

    input = "'a''\\a'#s"
    expected_value = "a'\\a"
    expected_style = "'"
    expected_suffix = '#s'

    value, style, suffix = dequote_yaml_string(input)
    assert(value == expected_value)
    assert(style == expected_style)
    assert(suffix == expected_suffix)

def test_double_quoted_escaping():
    """Double quotes with escape sequences.
    """

    input = '"\\\\\\"\\x20\\u0020\\U00000020"#s'
    expected_value = '\\"   '
    expected_style = '"'
    expected_suffix = '#s'

    value, style, suffix = dequote_yaml_string(input)
    assert(value == expected_value)
    assert(style == expected_style)
    assert(suffix == expected_suffix)

