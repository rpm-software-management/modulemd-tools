import os
import unittest
from unittest import mock
import yaml
from distutils.version import LooseVersion
from modulemd_tools.modulemd_tools.yaml import (
    is_valid, validate, create, update, dump, upgrade, _yaml2stream, _stream2yaml)

import gi
gi.require_version("Modulemd", "2.0")
from gi.repository import Modulemd  # noqa: E402


def old_libmodulemd():
    """
    Reading YAML string via `Modulemd.ModuleStream.read_string` and dumping it
    again encapsulates its value in double-quotes, and it messes up with some of
    our tests (since the older version does exactly the opposite). Let's just
    skip those few test on EPEL8 until it receives an update.
    See also `080e2bb`
    """
    return LooseVersion(Modulemd.get_version()) < LooseVersion("2.11.1")


class TestYaml(unittest.TestCase):

    def test_is_valid(self):
        self.assertTrue(is_valid(yaml1))
        self.assertFalse(is_valid(yaml2_invalid))

    def test_is_valid_wrong_format(self):
        self.assertFalse(is_valid("this is not yaml"))

    def test_validate(self):
        self.assertTrue(validate(yaml1))
        with self.assertRaises(Exception) as context:
            validate(yaml2_invalid)
        self.assertIn("The module and stream names are required",
                      str(context.exception))

    def test_validate_wrong_format(self):
        with self.assertRaises(RuntimeError) as context:
            validate("this is not yaml")
        self.assertIsInstance(context.exception, RuntimeError)
        self.assertIn("Unexpected YAML event in document stream",
                      str(context.exception))

    def test_create(self):
        result = create("foo", "stable")
        mod1 = yaml.safe_load(result)
        self.assertEqual(mod1["document"], "modulemd")
        self.assertEqual(mod1["version"], 2)
        self.assertEqual(mod1["data"]["name"], "foo")
        self.assertEqual(mod1["data"]["stream"], "stable")
        self.assertEqual(mod1["data"]["summary"], None)
        self.assertEqual(mod1["data"]["description"], "")
        self.assertEqual(mod1["data"]["license"]["module"], [None])

    def test_update_after_build(self):
        """
        This is an example modulemd transformation that copr-backend would do
        after finishing a module build.
        """
        # First, let's check that we can parse the modulemd YAML definition and
        # that it looks as expected
        mod1 = yaml.safe_load(yaml1)
        self.assertNotIn("arch", mod1["data"])
        for rpm in mod1["data"]["artifacts"]["rpms"]:
            self.assertTrue(rpm.startswith("LTK-"))

        # When copr-backend finishes a module build, it needs to update the
        # architecture and built artifacts
        rpms = ["foo-0:1.2-1.fc32.x86_64", "bar-1:1.2-3.fc32.x86_64"]
        result = update(yaml1, arch="x86_64", rpms_nevras=rpms)

        # Now let's see
        mod2 = yaml.safe_load(result)
        self.assertEqual(mod2["data"]["arch"], "x86_64")
        self.assertEqual(set(mod2["data"]["artifacts"]["rpms"]), set(rpms))

    def test_update_modulemd_creation(self):
        """
        This is an example modulemd transformation that copr-frontend would do
        when generating a new module via web UI (not exactly, but it would
        change these properties).
        """
        mod1 = yaml.safe_load(yaml1)
        self.assertEqual(mod1["data"]["version"], 123)
        self.assertEqual(mod1["data"]["context"], "f32")
        self.assertEqual(mod1["data"]["summary"], "Summary and stuff")
        self.assertEqual(mod1["data"]["description"],
                         "This module has been generated using dir2module tool")
        self.assertEqual(mod1["data"]["license"]["module"], ["MIT"])
        self.assertEqual(mod1["data"]["license"]["content"],
                         ["BSD", "GPLv2", "MIT"])

        result = update(yaml1, version=234, context="f33", summary="A new sum",
                        description="A new desc", module_licenses=["BSD"],
                        content_licenses=["MIT", "WTFPL"])

        mod1 = yaml.safe_load(result)
        self.assertEqual(mod1["data"]["version"], 234)
        self.assertEqual(mod1["data"]["context"], "f33")
        self.assertEqual(mod1["data"]["summary"], "A new sum")
        self.assertEqual(mod1["data"]["description"], "A new desc")
        self.assertEqual(set(mod1["data"]["license"]["module"]), {"BSD"})
        self.assertEqual(set(mod1["data"]["license"]["content"]),
                         {"MIT", "WTFPL"})

    def test_update_modulemd_nsvca(self):
        """
        It is not expected change module name or stream, not even `libmodulemd`
        classes allow it. In case you want to update a module name, you need to
        create a new one. I say f*ck it, let us change whatever we want.
        """
        mod1 = yaml.safe_load(yaml1)
        self.assertEqual(mod1["data"]["name"], "foo")
        self.assertEqual(mod1["data"]["stream"], "devel")
        self.assertEqual(mod1["data"]["version"], 123)
        self.assertEqual(mod1["data"]["context"], "f32")

        result = update(yaml1, name="bar", stream="stable",
                        version=234, context="f33")

        mod2 = yaml.safe_load(result)
        self.assertEqual(mod2["data"]["name"], "bar")
        self.assertEqual(mod2["data"]["stream"], "stable")
        self.assertEqual(mod2["data"]["version"], 234)
        self.assertEqual(mod2["data"]["context"], "f33")

        self.assertEqual(mod2["data"]["summary"], "Summary and stuff")
        self.assertEqual(mod1["data"]["license"]["module"], ["MIT"])

    def test_update_modulemd_dependencies(self):
        mod1 = yaml.safe_load(yaml1)
        deps1 = mod1["data"]["dependencies"][0]
        self.assertEqual(deps1["requires"], {"platform": ["f32"]})
        self.assertEqual(deps1["buildrequires"], {"platform": ["f32"]})

        result = update(yaml1, requires={"foo": ["f33"]},
                        buildrequires={"bar": ["master"]})

        mod2 = yaml.safe_load(result)
        deps2 = mod2["data"]["dependencies"][0]
        self.assertEqual(deps2["requires"], {"foo": ["f33"]})
        self.assertEqual(deps2["buildrequires"], {"bar": ["master"]})

    def test_update_modulemd_runtime_dependencies(self):
        """
        Dropping dependencies can be tricky so should rather make sure that if
        we want to update only runtime dependencies, the buildtime dependencies
        remain untouched.
        """
        mod1 = yaml.safe_load(yaml1)
        deps1 = mod1["data"]["dependencies"][0]
        self.assertEqual(deps1["requires"], {"platform": ["f32"]})
        self.assertEqual(deps1["buildrequires"], {"platform": ["f32"]})

        result = update(yaml1, requires={"foo": ["f33"]})

        mod2 = yaml.safe_load(result)
        deps2 = mod2["data"]["dependencies"][0]
        self.assertEqual(deps2["requires"], {"foo": ["f33"]})
        self.assertEqual(deps2["buildrequires"], {"platform": ["f32"]})

    def test_update_without_dependencies(self):
        """
        The logic for updating dependencies is a bit complicated and can fail
        when dependencies are not present in the modulemd YAML at all.
        """
        validate(yaml3_no_deps)
        mod1 = yaml.safe_load(yaml3_no_deps)
        self.assertNotIn("dependencies", mod1["data"])

        result = update(yaml3_no_deps, summary="Updated summary")
        mod2 = yaml.safe_load(result)
        self.assertEqual(mod2["data"]["summary"], "Updated summary")
        self.assertNotIn("dependencies", ["data"])

        result = update(yaml3_no_deps, requires={"foo": ["bar"]})
        mod3 = yaml.safe_load(result)
        self.assertEqual(mod3["data"]["dependencies"][0]["requires"],
                         {"foo": ["bar"]})

    def test_update_modulemd_with_multiple_pairs_of_deps(self):
        """
        While uncommon, it's not impossible for there to be more than one
        Dependencies object in the list.
        """
        validate(yaml6_multiple_pairs_of_deps)
        mod1 = yaml.safe_load(yaml6_multiple_pairs_of_deps)
        self.assertEqual(len(mod1["data"]["dependencies"]), 2)

        dependencies = [
            {"buildrequires": {"platform": ["-epel8"]},
             "requires": {"platform": ["-epel8"]}},
            {"buildrequires": {"libfoo": ["rolling"],
                               "platform": ["epel8"]},
             "requires": {"libfoo": ["rolling"],
                          "platform": ["epel8"]}},
        ]
        self.assertEqual(mod1["data"]["dependencies"], dependencies)

        requires = {"foo": ["bar"]}
        with self.assertRaises(AttributeError) as context:
            update(yaml6_multiple_pairs_of_deps, requires=requires)
        self.assertIn("Provided YAML contains multiple pairs of dependencies. "
                      "It is ambiguous which one to update.",
                      str(context.exception))

        buildrequires = {"baz": ["qux"]}
        with self.assertRaises(AttributeError) as context:
            update(yaml6_multiple_pairs_of_deps, buildrequires=buildrequires)
        self.assertIn("Provided YAML contains multiple pairs of dependencies. "
                      "It is ambiguous which one to update.",
                      str(context.exception))

        result = update(yaml6_multiple_pairs_of_deps,
                        requires=requires, buildrequires=buildrequires)
        mod2 = yaml.safe_load(result)
        self.assertEqual(len(mod2["data"]["dependencies"]), 1)
        self.assertEqual(mod2["data"]["dependencies"][0], {
            "requires": {"foo": ["bar"]},
            "buildrequires": {"baz": ["qux"]},
        })

    def test_update_modulemd_api(self):
        mod1 = yaml.safe_load(yaml1)
        self.assertNotIn("api", mod1["data"])

        result = update(yaml1, api=["foo", "bar"])
        mod2 = yaml.safe_load(result)
        self.assertEqual(set(mod2["data"]["api"]["rpms"]), {"foo", "bar"})

        result = update(result, api=["baz"])
        mod3 = yaml.safe_load(result)
        self.assertEqual(set(mod3["data"]["api"]["rpms"]), {"baz"})

    def test_update_modulemd_filters(self):
        mod1 = yaml.safe_load(yaml1)
        self.assertNotIn("filter", mod1["data"])

        result = update(yaml1, filters=["foo", "bar"])
        mod2 = yaml.safe_load(result)
        self.assertEqual(set(mod2["data"]["filter"]["rpms"]), {"foo", "bar"})

        result = update(result, filters=["baz"])
        mod3 = yaml.safe_load(result)
        self.assertEqual(set(mod3["data"]["filter"]["rpms"]), {"baz"})

    def test_update_modulemd_profiles(self):
        mod1 = yaml.safe_load(yaml1)
        self.assertNotIn("profiles", mod1["data"])

        profiles = {
            "default": ["foo"],
            "ubercool": ["foo", "bar"]
        }
        result = update(yaml1, profiles=profiles)
        mod2 = yaml.safe_load(result)
        self.assertEqual(len(mod2["data"]["profiles"]), 2)
        self.assertEqual(set(mod2["data"]["profiles"]["default"]["rpms"]),
                         {"foo"})
        self.assertEqual(set(mod2["data"]["profiles"]["ubercool"]["rpms"]),
                         {"foo", "bar"})

        result = update(result, profiles={"minimal": ["baz"]})
        mod3 = yaml.safe_load(result)
        self.assertEqual(len(mod3["data"]["profiles"]), 1)
        self.assertEqual(set(mod3["data"]["profiles"]["minimal"]["rpms"]),
                         {"baz"})

    def test_update_modulemd_components(self):
        mod1 = yaml.safe_load(yaml1)
        self.assertNotIn("components", mod1["data"])

        components = [
            {"name": "foo", "rationale": "Just because", "buildorder": 10},
            {"name": "bar", "rationale": "It's a dep"},
        ]
        result = update(yaml1, components=components)
        mod2 = yaml.safe_load(result)
        self.assertEqual(len(mod2["data"]["components"]["rpms"]), 2)
        self.assertEqual(mod2["data"]["components"]["rpms"]["foo"], {
            "rationale": "Just because",
            "buildorder": 10,
        })
        self.assertEqual(mod2["data"]["components"]["rpms"]["bar"], {
            "rationale": "It's a dep",
        })

        components = [{
            "name": "baz",
            "rationale": "Testing component properties",
            "buildorder": 20,
            "ref": "master",
            "repository": "http://foo.bar/baz.git",
        }]
        result = update(result, components=components)
        mod2 = yaml.safe_load(result)
        self.assertEqual(len(mod2["data"]["components"]["rpms"]), 1)
        baz = mod2["data"]["components"]["rpms"]["baz"]
        self.assertEqual(baz, {
            "rationale": "Testing component properties",
            "buildorder": 20,
            "ref": "master",
            "repository": "http://foo.bar/baz.git",
        })

    def test_upgrade(self):
        result = upgrade(yaml4_v1, 2)
        mod_stream = _yaml2stream(result)
        self.assertEqual(mod_stream.get_mdversion(), 2)
        self.assertEqual(mod_stream.get_module_name(), "")
        self.assertEqual(mod_stream.get_summary(),
                         "A test module in all its beautiful beauty")

    @unittest.skipIf(old_libmodulemd(), "Old modulemd drops stream value quotes")
    def test_upgrade_to_same_version(self):
        result = upgrade(yaml1, 2)
        self.assertEqual(result, yaml1)

    def test_upgrade_cannot_downgrade(self):
        with self.assertRaises(ValueError) as context:
            upgrade(yaml1, 1)
        self.assertIn("Cannot downgrade modulemd version",
                      str(context.exception))

    def test_upgrade_empty_yaml(self):
        for mod_yaml in [None, "", "foo: bar"]:
            with self.assertRaises(ValueError) as context:
                upgrade(mod_yaml, 2)
            self.assertIn("Missing modulemd version", str(context.exception))

    def test_upgrade_unexpected_version(self):
        # Neither current modulemd version cannot be unexpected
        with self.assertRaises(ValueError) as context:
            upgrade("version: 5", 2)
        self.assertIn("Unexpected modulemd version", str(context.exception))

        # Nor the wanted one
        with self.assertRaises(ValueError) as context:
            upgrade("version: 1", 5)
        self.assertIn("Unexpected modulemd version", str(context.exception))

    def test_dump(self):
        with mock.patch("builtins.open") as mock_open:
            dump(yaml1)
            mock_open.assert_called_once()
            path = os.path.join(os.getcwd(),
                                "foo:devel:123:f32:noarch.modulemd.yaml")
            self.assertEqual(mock_open.call_args[0][0], path)

        with mock.patch("builtins.open") as mock_open:
            dump(yaml1, dest="/tmp")
            mock_open.assert_called_once()
            path = "/tmp/foo:devel:123:f32:noarch.modulemd.yaml"
            self.assertEqual(mock_open.call_args[0][0], path)

        with mock.patch("builtins.open") as mock_open:
            dump(yaml1, dest="/tmp/testmodule.yaml")
            mock_open.assert_called_once()
            self.assertEqual(mock_open.call_args[0][0], "/tmp/testmodule.yaml")

    def test_yaml2stream(self):
        mod_stream = _yaml2stream(yaml1)
        self.assertEqual(mod_stream.get_module_name(), "foo")
        self.assertEqual(mod_stream.get_summary(), "Summary and stuff")

        with self.assertRaises(ValueError) as context:
            _yaml2stream("")
        self.assertIn("YAML didn't begin with STREAM_START.",
                      str(context.exception))

        with self.assertRaises(ValueError) as context:
            _yaml2stream(yaml5_multiple_streams)
        self.assertIn("YAML contained more than a single subdocument",
                      str(context.exception))

        with self.assertRaises(ValueError) as context:
            _yaml2stream(yaml5_multiple_modules)
        self.assertIn("YAML contained more than a single subdocument",
                      str(context.exception))

    @unittest.skipIf(old_libmodulemd(), "Old modulemd drops stream value quotes")
    def test_stream2yaml(self):
        mod_stream = _yaml2stream(yaml1)
        self.assertEqual(_stream2yaml(mod_stream), yaml1)

        mod_stream.set_summary(None)
        with self.assertRaises(RuntimeError) as context:
            _stream2yaml(mod_stream)
        self.assertIn("Could not validate stream to emit: Summary is missing",
                      str(context.exception))


yaml1 = """---
document: modulemd
version: 2
data:
  name: foo
  stream: "devel"
  version: 123
  context: f32
  summary: Summary and stuff
  description: >-
    This module has been generated using dir2module tool
  license:
    module:
    - MIT
    content:
    - BSD
    - GPLv2
    - MIT
  dependencies:
  - buildrequires:
      platform: [f32]
    requires:
      platform: [f32]
  artifacts:
    rpms:
    - LTK-0:1.5.0-8.fc32.x86_64
    - LTK-debuginfo-0:1.5.0-8.fc32.x86_64
    - LTK-debugsource-0:1.5.0-8.fc32.x86_64
...
"""


# Invalid because of missing name
yaml2_invalid = """
---
document: modulemd
version: 2
data:
  stream: "devel"
  version: 123
  context: f32
  summary: Summary and stuff
  description: >-
    This module has been generated using dir2module tool
  license:
    module:
    - MIT
    content:
    - BSD
    - GPLv2
    - MIT
  dependencies:
  - {}
  artifacts:
    rpms:
    - LTK-0:1.5.0-8.fc32.x86_64
    - LTK-debuginfo-0:1.5.0-8.fc32.x86_64
    - LTK-debugsource-0:1.5.0-8.fc32.x86_64
...
"""


# Doesn't have any buildrequires nor requires, still a valid modulemd though
yaml3_no_deps = """
---
document: modulemd
version: 2
data:
  name: foo
  stream: "devel"
  version: 123
  context: f32
  summary: Summary and stuff
  description: >-
    This module has been generated using dir2module tool
  license:
    module:
    - MIT
    content:
    - BSD
    - GPLv2
    - MIT
  artifacts:
    rpms:
    - LTK-0:1.5.0-8.fc32.x86_64
    - LTK-debuginfo-0:1.5.0-8.fc32.x86_64
    - LTK-debugsource-0:1.5.0-8.fc32.x86_64
...
"""


# This is a module in modulemd v1 format, taken from
# https://src.fedoraproject.org/modules/testmodule/raw/fancy/f/testmodule.yaml
# I just cropped the description a bit.
yaml4_v1 = """
document: modulemd
version: 1
data:
    summary: A test module in all its beautiful beauty
    description: This module demonstrates how to write simple modulemd files
    license:
        module: [ MIT ]
    dependencies:
        buildrequires:
            platform: f33
        requires:
            platform: f33
    references:
        community: https://fedoraproject.org/wiki/Modularity
        documentation: https://fedoraproject.org/wiki/Fedora_Packaging_Guidelines_for_Modules
        tracker: https://taiga.fedorainfracloud.org/project/modularity
    profiles:
        default:
            rpms:
                - tangerine
    api:
        rpms:
            - perl-Tangerine
            - tangerine
    components:
        rpms:
            perl-List-Compare:
                rationale: A dependency of tangerine.
                ref: master
        modules:
            dwm:
                rationale: Testing module inclusion.
                ref: 6.1
                buildorder: 10
"""


# A merged YAML containing multiple streams of one module
yaml5_multiple_streams = """
---
document: modulemd
version: 2
data:
  name: foo
  stream: "master"
  version: 1
  summary: A test module in all its beautiful beauty
  description: >-
    Some description
  license:
    module:
    - MIT
...
---
document: modulemd
version: 2
data:
  name: foo
  stream: "stable"
  version: 123
  context: f32
  summary: Summary and stuff
  description: >-
    This module has been generated using dir2module tool
  license:
    module:
    - MIT
...
"""


# A merged YAML containing multiple modules
yaml5_multiple_modules = """
---
document: modulemd
version: 2
data:
  name: foo
  stream: "master"
  version: 1
  summary: A test module in all its beautiful beauty
  description: >-
    Some description
  license:
    module:
    - MIT
...
---
document: modulemd
version: 2
data:
  name: bar
  stream: "stable"
  version: 123
  context: f32
  summary: Summary and stuff
  description: >-
    This module has been generated using dir2module tool
  license:
    module:
    - MIT
...
"""


# A module with multiple pairs of dependencies
yaml6_multiple_pairs_of_deps = """
---
document: modulemd
version: 2
data:
  name: foo
  stream: "master"
  version: 1
  summary: A test module in all its beautiful beauty
  description: >-
    Some description
  license:
    module:
    - MIT
  dependencies:
  - buildrequires:
      platform: [ -epel8 ]
    requires:
      platform: [ -epel8 ]
  - buildrequires:
      platform: [ epel8 ]
      libfoo: [ rolling ]
    requires:
      platform: [ epel8 ]
      libfoo: [ rolling ]
...
"""


if __name__ == '__main__':
    unittest.main()
