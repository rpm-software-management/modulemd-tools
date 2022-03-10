from modulemd_tools.modulemd_add_platform.modulemd_add_platform \
    import process_string
import logging

logger = logging.getLogger('null')
logger.setLevel(logging.CRITICAL + 1)


def test_positive():
    input = """
    document: modulemd-packager
    version: 3
    data:
    # Many spaces
        configurations :
            # Comment A
        - context: 'A'
             # Inter comment
          platform: f34
           # Trailing comment
        - context: 'B'
          platform: f35
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
    # Many spaces
        configurations :
            # Comment A
        - context: 'A'
             # Inter comment
          platform: f34
           # Trailing comment
        - context: 'B'
          platform: f35
        - context: 'f36'
          platform: f36
    """

    error, output = process_string(logger, input, False, 'f35', 'f36')
    assert(error == 0)
    assert(output == expected)


def test_positive_the_last_line():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
"""
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
        - context: 'B'
          platform: B
"""

    error, output = process_string(logger, input, False, 'A', 'B')
    assert(error == 0)
    assert(output == expected)


def test_positive_no_trailing_newline():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A"""
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
        - context: 'B'
          platform: B"""

    error, output = process_string(logger, input, False, 'A', 'B')
    assert(error == 0)
    assert(output == expected)


def test_invalid_input_document():
    input = """
    document: gibberish
    version: 3
    data:
    """
    error, output = process_string(logger, input, False, 'f35', 'f36')
    assert(error == 1)


def test_no_old_platform():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: 'A'
    """
    error, output = process_string(logger, input, False, 'f35', 'f36')
    assert(error == 2)


def test_new_platform_exists():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: 'A'
        - context: 'B'
          platform: 'B'
    """
    error, output = process_string(logger, input, False, 'B', 'B')
    assert(error == -1)


def test_positive_with_comments():
    input = """
    document: modulemd-packager
    version: 3
    data:
    # Many spaces
        configurations :
            # Comment A
        - context: 'A' # Context suffix comment
             # Inter comment
          platform: A  # Platform suffix comment
           # Trailing comment
        - context: 'B'
          platform: B
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
    # Many spaces
        configurations :
            # Comment A
        - context: 'A' # Context suffix comment
             # Inter comment
          platform: A  # Platform suffix comment
           # Trailing comment
        - context: 'X' # Context suffix comment
             # Inter comment
          platform: X  # Platform suffix comment
           # Trailing comment
        - context: 'B'
          platform: B
    """

    error, output = process_string(logger, input, False, 'A', 'X')
    assert(error == 0)
    assert(output == expected)


def test_positive_conflicting_context():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
        - context: 'B'
          platform: C
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
        - context: '0'
          platform: B
        - context: 'B'
          platform: C
    """

    error, output = process_string(logger, input, False, 'A', 'B')
    assert(error == 0)
    assert(output == expected)


def test_positive_multiple_contexts():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
        - context: 'B'
          platform: A
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
        - context: '0'
          platform: B
        - context: 'B'
          platform: A
        - context: '1'
          platform: B
    """

    error, output = process_string(logger, input, False, 'A', 'B')
    assert(error == 0)
    assert(output == expected)


def test_positive_new_platform_is_invalid_context():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: A
        - context: '0'
          platform: 1.2
    """

    error, output = process_string(logger, input, False, 'A', '1.2')
    assert(error == 0)
    assert(output == expected)


def test_positive_nested_fields_inside_a_context():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
            - context: 'A'
              platform: A
              buildrequires:
                  foo: [bar]
    """
    expected = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
            - context: 'A'
              platform: A
              buildrequires:
                  foo: [bar]
            - context: 'B'
              platform: B
              buildrequires:
                  foo: [bar]
    """

    error, output = process_string(logger, input, False, 'A', 'B')
    assert(error == 0)
    assert(output == expected)
