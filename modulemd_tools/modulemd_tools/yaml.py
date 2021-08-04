"""
Module for working with modulemd YAML definitions with the least abstractions as
possible. Within this module, modulemd YAMLs are represented simply as a string,
and all transformation functions are `str` -> `str`.
"""

import os
import gi
import yaml

gi.require_version("Modulemd", "2.0")
from gi.repository import Modulemd  # noqa: E402


def is_valid(mod_yaml):
    """
    Determine whether the `mod_yaml` string is a valid modulemd YAML definition
    """
    idx = Modulemd.ModuleIndex.new()
    try:
        ret, _ = idx.update_from_string(mod_yaml, strict=True)
        return ret
    except gi.repository.GLib.GError:
        return False


def validate(mod_yaml):
    """
    Same as `is_valid` but raises exception if the YAML is not valid.
    """
    idx = Modulemd.ModuleIndex.new()
    try:
        ret, failures = idx.update_from_string(mod_yaml, strict=True)
    except gi.repository.GLib.GError as ex:
        raise RuntimeError(ex)
    if not ret:
        raise RuntimeError(failures[0].get_gerror().message)
    return ret


def create(name, stream):
    """
    Create a minimal modulemd YAML definition containing only a module name and
    module stream. To set any additional attributes, use `update` function.
    """
    mod_stream = Modulemd.ModuleStreamV2.new(name, stream)
    mod_stream.set_summary("")
    mod_stream.set_description("")
    mod_stream.add_module_license("")
    index = Modulemd.ModuleIndex.new()
    index.add_module_stream(mod_stream)
    return index.dump_to_string()


def update(mod_yaml, name=None, stream=None, version=None, context=None,
           arch=None, summary=None, description=None, module_licenses=None,
           content_licenses=None, rpms_nevras=None, requires=None,
           buildrequires=None, api=None, filters=None, profiles=None,
           components=None):
    """
    Transform a given modulemd YAML string into another, updated one. The input
    string remains unchanged.

    This function allows to modify specified modulemd attributes while leaving
    the rest of them as is. For structured attributes, such as `module_licenses`
    which value is a list, new values are not appended to a list, but the new
    value is used instead.

    For the official documentation of the modulemd YAML format and it's values,
    please see
    https://github.com/fedora-modularity/libmodulemd/blob/main/yaml_specs/modulemd_stream_v2.yaml
    It will allow you to better understand the parameters of this function.

    Args:
        mod_yaml (str): An input modulelmd YAML
        name (str): The name of the module
        stream (str): Module update stream name
        version (int): Module version, integer, cannot be negative
        context (str): Module context flag
        arch (str): Module artifact architecture
        summary (str): A short summary describing the module
        description (str): A verbose description of the module
        module_licenses (list): A list of module licenses
        content_licenses (list): A list of licenses used by the packages in
            the module.
        rpms_nevras (list): RPM artifacts shipped with this module
        requires (dict): Module runtime dependencies represented as a `dict` of
            module names as keys and list of streams as their values.
        buildrequires (dict): Module buildtime dependencies represented as a
            `dict` of module names as keys and list of streams as their values.
        api (list): The module's public RPM-level API represented as a list of
            package names.
        filters (list): Module component filters represented as a list of pckage
            names.
        profiles (dict): A `dict` of profile names as keys and lists of package
            names as their values.
        components (list): Functional components of the module represented as a
            `dict` with package names as keys and `dict`s representing the
            particular components as keys. The component `dict` should contain
            keys like `name`, `rationale`, `repository`, etc.

    Returns:
        An updated modulemd YAML represented as string

    """
    mod_stream = _yaml2stream(mod_yaml)
    name = name or mod_stream.get_module_name()
    stream = stream or mod_stream.get_stream_name()
    mod_stream = Modulemd.read_packager_string(mod_yaml, name, stream)

    if version:
        mod_stream.set_version(version)

    if context:
        mod_stream.set_context(context)

    if arch:
        mod_stream.set_arch(arch)

    if summary:
        mod_stream.set_summary(summary)

    if description:
        mod_stream.set_description(description)

    if module_licenses:
        mod_stream.clear_module_licenses()
        for module_license in module_licenses:
            mod_stream.add_module_license(module_license)

    if content_licenses:
        mod_stream.clear_content_licenses()
        for content_license in content_licenses:
            mod_stream.add_content_license(content_license)

    if rpms_nevras:
        mod_stream.clear_rpm_artifacts()
        for nevra in rpms_nevras:
            mod_stream.add_rpm_artifact(nevra)

    if api:
        mod_stream.clear_rpm_api()
        for rpm in api:
            mod_stream.add_rpm_api(rpm)

    if filters:
        mod_stream.clear_rpm_filters()
        for rpm in filters:
            mod_stream.add_rpm_filter(rpm)

    if profiles:
        mod_stream.clear_profiles()
        for profile_name, rpms in profiles.items():
            profile = Modulemd.Profile.new(profile_name)
            for rpm in rpms:
                profile.add_rpm(rpm)
            mod_stream.add_profile(profile)

    if components:
        mod_stream.clear_rpm_components()
        for component in components:
            component_rpm = Modulemd.ComponentRpm.new(component.pop("name"))
            for key, value in component.items():
                component_rpm.set_property(key, value)
            mod_stream.add_component(component_rpm)

    # Updating dependencies is quite messy because AFAIK the only operations
    # that `libmodoulemd` allows us to do is adding a runtime/buildtime
    # dependencies one be one and dropping all of them at once.
    # We need to help ourselves a little and drop all runtime dependencies and
    # re-populate them with the old ones if a new ones weren't set. Similarly
    # for buildrequires.
    old_deps = Modulemd.Dependencies()

    # Module can contain multiple pairs of dependencies. If we want to update
    # both `requires` and `buildrequires` at the same time, we can drop all
    # current dependencies and just set a new one. If we want to update only
    # one of them, we are getting to an ambiguous situation, not knowing what
    # pair of dependencies we should update. Let's just raise an exception.
    if (len(mod_stream.get_dependencies()) > 1
            and (requires or buildrequires)
            and not (requires and buildrequires)):
        raise AttributeError("Provided YAML contains multiple pairs of "
                             "dependencies. It is ambiguous which one to "
                             "update.")

    if mod_stream.get_dependencies():
        old_deps = mod_stream.get_dependencies()[0]
    new_deps = Modulemd.Dependencies()
    if requires:
        for depname, depstreams in requires.items():
            for depstream in depstreams:
                new_deps.add_runtime_stream(depname, depstream)
    else:
        for depname in old_deps.get_runtime_modules():
            for depstream in old_deps.get_runtime_streams(depname):
                new_deps.add_runtime_stream(depname, depstream)

    if buildrequires:
        for depname, depstreams in buildrequires.items():
            for depstream in depstreams:
                new_deps.add_buildtime_stream(depname, depstream)
    else:
        for depname in old_deps.get_buildtime_modules():
            for depstream in old_deps.get_buildtime_streams(depname):
                new_deps.add_buildtime_stream(depname, depstream)

    if requires or buildrequires:
        mod_stream.clear_dependencies()
        mod_stream.add_dependencies(new_deps)

    idx2 = Modulemd.ModuleIndex.new()
    idx2.add_module_stream(mod_stream)
    return idx2.dump_to_string()


def upgrade(mod_yaml, version):
    """
    Upgrade the input module YAML from an older version to a newer one.
    Downgrades aren't supported even in case where it would be possible.
    """
    parsed = yaml.safe_load(mod_yaml or "")
    if not parsed or "version" not in parsed:
        raise ValueError("Missing modulemd version")

    supported = [1, 2]
    if parsed["version"] not in supported or version not in supported:
        raise ValueError("Unexpected modulemd version")

    if parsed["version"] > version:
        raise ValueError("Cannot downgrade modulemd version")

    mod_stream = Modulemd.read_packager_string(
        mod_yaml,
        parsed["data"].get("name", ""),
        parsed["data"].get("stream", ""))

    mod_upgraded = mod_stream.upgrade_ext(version)
    mod_stream_upgraded = mod_upgraded.get_stream_by_NSVCA(
        mod_stream.get_stream_name(),
        mod_stream.get_version(),
        mod_stream.get_context(),
        mod_stream.get_arch())

    return _stream2yaml(mod_stream_upgraded)


def load(path):
    """
    Load modulemd YAML definition from a file
    """
    with open(path, "r") as yaml_file:
        mod_yaml = yaml_file.read()
    validate(mod_yaml)
    return mod_yaml


def dump(mod_yaml, dest=None):
    """
    Dump modulemd YAML definition into a file

    If `dest` is not specified, the file will be created in the current working
    directory and it's name is going to be generated from the module attributes
    in the `N:S:V:C:A.modulemd.yaml` format.

    If `dest` is a directory, then the file is going to be generated in that
    directory.

    If `dest` is pointing to a (nonexisting) file, it is going to be dumped in
    its place.
    """
    filename = _generate_filename(mod_yaml)

    path = dest
    if not path:
        path = os.path.join(os.getcwd(), filename)
    elif os.path.isdir(path):
        path = os.path.join(dest, filename)

    with open(path, "w") as moduleyaml:
        moduleyaml.write(mod_yaml)


def _generate_filename(mod_yaml):
    """
    Generate filename for a module yaml
    """
    mod_stream = _yaml2stream(mod_yaml)
    return "{N}:{S}:{V}:{C}:{A}.modulemd.yaml".format(
        N=mod_stream.get_module_name(),
        S=mod_stream.get_stream_name(),
        V=mod_stream.get_version(),
        C=mod_stream.get_context(),
        A=mod_stream.get_arch() or "noarch")


def _yaml2stream(mod_yaml):
    try:
        return Modulemd.read_packager_string(mod_yaml)
    except gi.repository.GLib.GError as ex:
        raise ValueError(ex.message)


def _stream2yaml(mod_stream):
    idx = Modulemd.ModuleIndex.new()
    idx.add_module_stream(mod_stream)
    try:
        return idx.dump_to_string()
    except gi.repository.GLib.GError as ex:
        raise RuntimeError(ex.message)
