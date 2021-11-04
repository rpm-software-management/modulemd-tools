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

