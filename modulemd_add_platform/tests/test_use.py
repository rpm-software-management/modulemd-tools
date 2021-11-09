import pytest
from modulemd_add_platform.modulemd_add_platform import process_string

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

    error, output = process_string(input, 'f35', 'f36')
    assert(error == 0)
    assert(output == expected)

def test_no_old_platform():
    input = """
    document: modulemd-packager
    version: 3
    data:
        configurations:
        - context: 'A'
          platform: 'A'
    """
    error, output = process_string(input, 'f35', 'f36')
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
    error, output = process_string(input, 'B', 'B')
    assert(error == -1)

def test_positive_with_comments():
    input = """
    document: modulemd-packager
    version: 3
    data:
    # Many spaces
        configurations :
            # Comment A
        - context: 'A'
             # Inter comment
          platform: A
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
        - context: 'A'
             # Inter comment
          platform: A
           # Trailing comment
        - context: 'X'
             # Inter comment
          platform: X
           # Trailing comment
        - context: 'B'
          platform: B
    """

    error, output = process_string(input, 'A', 'X')
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

    error, output = process_string(input, 'A', 'B')
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

    error, output = process_string(input, 'A', 'B')
    assert(error == 0)
    assert(output == expected)

