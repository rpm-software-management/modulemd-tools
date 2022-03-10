from textwrap import dedent

import pytest


@pytest.fixture
def dummy_module():
    return {
        'name': 'dummy',
        'stream': '0',
        'version': 1,
        'context': '2',
        'arch': 'noarch',
        'summary': 'Dummy Module',
        'description': 'One dummy module for your tests',
        'module_license': 'No License',
        'licenses': [],
        'packages': [],
        'requires': {}
    }


@pytest.fixture
def dummy_module_mmd_as_string():
    return dedent("""
        ---
        document: modulemd
        version: 2
        data:
          name: dummy
          stream: 0
          version: 1
          context: 2
          summary: Dummy Module
          description: >-
            One dummy module for your tests
          license:
            module:
            - No License
          dependencies:
          - {}
        ...
    """).lstrip()
