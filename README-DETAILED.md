# repo2module

Generates `modules.yaml` file with a module, that provides all RPM
packages that are available within a repository. Which can be a first
step towards converting the repository to a modular repository, please
see [Creating a module repository from a regular repository][repo2modrepo].

Besides a path to a YUM repository, also module information such as
its `name`, `stream`, `version`, and `context` is required.


## Usage

Assuming there is a YUM repository in your current working directory.

```
$ ls
hello-2.8-1.fc32.x86_64.rpm  repodata
```

You can generate a module providing its packages with:

```
$ repo2module . \
    --module-name foo \
    --module-stream devel \
    --module-version 123 \
    --module-context f32
```

Please always manually review (and edit) the generated `modules.yaml` file
before using it.



[repo2modrepo]: ../README.md#creating-a-module-repository-from-a-regular-repository

# dir2module

`dir2module` operates over a directory of RPM packages. There are no
additional constraints, the directory **doesn't** have to be a YUM
repository and there doesn't have to be anything special about those
RPM packages, they can be built by any standard tool such as
`rpmbuild`, `mock`, or any build-system such as [Koji][koji] or
[Copr][copr]. The `dir2module` then recursively finds all RPM packages and
generates a module definition that provides them.

Besides the directory path, some module information needs to be passed to the
`dir2module` tool so it can properly generate a module definition. A module
`name`, `stream`, `version`, `context`, and `arch` are expected as one parameter
in an `N:S:V:C:A` format and module summary is expected as well. For more
information about these properties, please see the [Modularity docs][nsvca].

By default, the output is dumped into a file (in the current working directory)
named `N:S:V:C:A.modulemd.yaml`. Alternatively, the output can be written into
the stdout.


## How is the module generated?

Besides the `N:S:V:C:A` and summary which is taken from input parameters and
written to the module definition as is, also other module information is
generated based on it.

Module `description` is a required field and therefore is filled with a
placeholder text. By default, the module license is [MIT][MIT] but can be
overwritten via a command-line parameter. Licenses of the module's contents are
generated from the set of individual packages that are to be provided by the
module. The actual packages are set as [module artifacts][artifacts].

Please always manually review (and edit) the generated YAML file before using
it.


## Usage

The very-standard usage is to generate modulemd YAML file for all packages in
the current directory.

```
$ dir2module foo:devel:123:f32:x86_64 -m "My example module" --dir .
```

To dump the output to the STDOUT instead of a file.

```
$ dir2module foo:devel:123:f32:x86_64 -m "My example module" --dir . --stdout
```

To define a list of module packages manually, instead of searching for them in a
directory.

```
$ cat foo-devel.pkglist
foo-2.8-1.fc32.x86_64.rpm
bar-1.2-3.fc32.x86_64.rpm
baz-2.3-4.fc32.x86_64.rpm

$ dir2module foo:devel:123:f32:x86_64 \
    -m "My example module" \
    --pkglist foo-deve.pkglist
```


## Debug

You will most likely encounter the following error.
```
WARNING: RPM does not have `modularitylabel` header set: ./foo-2.8-1.fc32.x86_64.rpm
Error: All packages need to contain the `modularitylabel` header.
To suppress this constraint, use `--force` parameter
```

That's because module RPM packages should contain a `modularitylabel` header,
please see the [Modules – Fake it till you make it][modularity-label] blogpost
from [@sgallagher][sgallagher].

Feel free to suppress this warning by using `--force` parameter.

To resolve this issue _properly_ and without requiring to modify your package
spec file, just rebuild the package with `modularitylabel` macro defined. The
macro is case-sensitive, so please make sure that it is all lowercase.

```
mock -r fedora-32-x86_64 /path/to/hello-2.8-2.fc32.src.rpm \
    --define "modularitylabel foo:devel:123:f32"
```



[koji]: https://koji.fedoraproject.org
[copr]: https://copr.fedorainfracloud.org/
[nsvca]: https://docs.fedoraproject.org/en-US/modularity/architecture/nsvca/
[MIT]: https://opensource.org/licenses/MIT
[RFE]: https://bugzilla.redhat.com/show_bug.cgi?id=1801747#c7
[artifacts]: https://docs.fedoraproject.org/en-US/modularity/architecture/#_artifacts
[sgallagher]: https://github.com/sgallagher
[modularity-label]: https://sgallagh.wordpress.com/2019/08/14/sausage-factory-modules-fake-it-till-you-make-it/

# createrepo_mod

A small wrapper around `createrepo_c` and `modifyrepo_c` to provide an easy tool
for generating module repositories.

This tool can be used as a drop-in replacement for `createrepo_c` with
one caveat. You need to specify `<directory>` before `[options]`.
Otherwise it works fine with both module and non-module repositories.

Please see `man createrepo_c` for the complete list of possible
command-line arguments and their meaning. `createrepo_mod` doesn't
define or redefine any of the original `createrepo_c` arguments.


## Creating a modular repository

Please see the official Fedora Modularity documentation for the reference of how
module repositories should be created

https://docs.fedoraproject.org/en-US/modularity/hosting-modules/

Even though the process of creating modular repositories takes only
few simple steps, from user perspective the whole action is atomic.
That's where `createrepo_mod` fits in.


## Usage

First navigate to a directory that is to become a repository. You
should have some RPM packages in there. In order to create a modular
repository (instead of a normal one), you need to put a module YAML
file into the directory.

```
$ ls -1
foo-1.0.fc33.noarch.rpm
foo:devel:123:f32:x86_64.modulemd.yaml
```

There can be multiple RPM files in the directory (which is no
surprise) but there can also be multiple module YAML files. Gziped
YAML files, e.g. `foo:devel:123:f32:x86_64.modulemd.yaml.gz` are also
suppoprted. Each `.yaml` and `.yaml.gz` in the directory is examined
and used only if it a valid [modulemd document], otherwise it is
skipped. Please see
https://github.com/fedora-modularity/libmodulemd/blob/main/yaml_specs/modulemd_stream_v2.yaml

Having RPM packages and module YAML documents, simply run

```
$ createrepo_mod .
```


## Debug

If you are having troubles with module repositories not working, check
your generated `repodata` directory. There should be a compressed file
with module metadata.

```
$ ls repodata/*-modules.yaml.gz
repodata/34bd2ebb4de3e21644b351d06b59783dcd1aa751b035bbb31da70fa62dbb8e97-modules.yaml.gz
```

If it is missing you either didn't put a valid modulemd YAML document
into your repo directory or you have encountered a bug in
`createrepo_mod` tool.

Also, the initial module YAML files in the repo directory required for
repo generation (e.g. `foo:devel:123:f32:x86_64.modulemd.yaml.gz`) and
`modules.yaml` file generated by `createrepo_mod` run are not
necessary for the repo to work and can be safely removed. They might
be useful for a repo re-generation though. The only important thing is
the content of `repodata` directory.


## Future

This is supposed to be only a temporary solution, in the future we would like to
have the modularity support implemented in `createrepo_c` itself. See

https://bugzilla.redhat.com/show_bug.cgi?id=1816753

This feature is built-in in the `createrepo_c` itself since 0.16.1 version.

# modulemd-add-platform

This tool edits a modulemd-packager YAML document.
It copies contexts of an old platform to new contexts of a new platform.
A file with the modulemd-packager YAML document is overrided.
If a context for the new platform already exists, nothing is done.
If a context for the old platform does not exist, an error is reported.

Hint: A platform specifies against what distribution and its release the
module should be built against (for example `f35`, `epel9`, etc).

# modulemd-merge

### Merge multiple modulemd YAML files into one

This is useful for example if you have several yum repositories and want
to merge them into one. If they are module-enabled, you also have to merge
their `modules.yaml` files (linked in the `repomd.xml`). Otherwise, the
modularity system will break for them, as the moduled RPMs won't be filtered
properly anymore.

Another use-case is if you want to mirror a yum repository and the source
expires older files, but you want to keep these expired files locally, for
example, to allow downgrades. modulemd-merge can then be used to merge the
previous modules.yaml file with the new one after each mirror update.
This way the module information for the expired rpms is preserved.


### Usage

```
modulemd-merge [-h] [-v] [-d] [-i] input [input ...] output

positional arguments:

input:
  input filename(s) or directories.

  repomd.xml files are parsed and modules hrefs contained are merged.
  If a directory is given, it is searched for repodata/repomd.xml and repomd.xml

output:
  YAML output filename

optional arguments:

  -h, --help            output the help text

  -v, --verbose         increase output verbosity

  -d, --debug           debug output verbosity

  -i, --ignore-no-input
                        ignore non-existing input files
```

Usage example

```
$ modulemd-merge -i \
    foo:devel:123:f32:x86_64.modulemd.yaml \
    bar:stable:234:f32:x86_64.modulemd.yaml \
    modules.yaml
```

# modulemd-generate-macros

Generate `module-build-macros` SRPM package, which is a central piece
for building modules. It should be present in the buildroot before any
other module packages are submitted to be built. It redefines some
existing macros such as `%{dist}` and creates some new ones, such as
`%{modularitylabel}` (which tells DNF to not update the package from a
non-modular version).


## Usage

The usage is straightforward, just run the `modulemd-generate-macros`
tool and give it a modulemd YAML file.

```
$ modulemd-generate-macros foo:devel:123:f32:x86_64.modulemd.yaml
```

If necessary, it is possible to specify desired disttag.

```
$ modulemd-generate-macros foo:devel:123:f32:x86_64.modulemd.yaml --disttag .fc33
```

In more advanced case, conflicting packages can be specified. Let's
assume following file named `conflicts.txt`

```
$ cat conflicts.txt
# Filter out RPMs from stream collision

Conflicts: foo = 0:1-1
Conflicts: bar = 0:2-1

# Filter out base module RPMs that overlap
# with the RPMs in the buildrequired modules

Conflicts: baz = 1:2-3
```

Then it can be injected into the `module-build-macros.spec` with

```
$ modulemd-generate-macros foo:devel:123:f32:x86_64.modulemd.yaml \
	--conflicts-from-file ./conflicts
```


## Debug

### Wrong modulemd YAML file

The specified file needs to be a valid modulemd YAML file, please see its
[specification][modulemd-spec]. Please note that this tool parses a single YAML
file, it doesn't consider whether it is a part of a repository (yet?) and
therefore some mandatory options, that are described as `AUTOMATIC` needs to be
filled in the document (e.g. `name`, `stream`, `version`, `context`, and
`arch`). Otherwise, something like this error might appear.

```
$ modulemd-generate-macros foo:devel:123:f32:x86_64.modulemd.yaml
Failed to parse ../createrepo_mod/foo:devel:123:f32:x86_64.modulemd.yaml
Make sure it is a valid modulemd YAML file

Hint: The module and stream names are required when adding to ModuleIndex.
```

### Wrong parameter passed

In case you specify a syntactically incorrect disttag or conflicting packages,
you might get this error.

```
$ modulemd-generate-macros foo:devel:123:f32:x86_64.modulemd.yaml --disttag ".#{foo}"
warning: line 11: Possible unexpanded macro in: Release:    1.#{foo}
error: line 11: Illegal char '#' (0x23) in: Release:    1.#{foo}

Failed to generate module-build-macros SRPM package

Command '['rpmbuild', '-bs', 'module-build-macros.spec', '--define',
'_topdir /tmp/module_build_service-build-macrosyicmdp1l', '--define',
'_sourcedir /tmp/module_build_service-build-macrosyicmdp1l/SOURCES']'
returned non-zero value 1, stdout log: /dev/null

Please review /tmp/module_build_service-build-macrosyicmdp1l/module-build-macros.spec
```

The recommended way to solve the issue is by reviewing the generated spec file
and making sure it is valid.


## See also

- [RFE for this tool][RFE]
- [RFE for MBS requesting this tool][RFE-mbs]



[modulemd-spec]: https://github.com/fedora-modularity/libmodulemd/blob/main/yaml_specs/modulemd_stream_v2.yaml
[RFE]: https://github.com/rpm-software-management/modulemd-tools/issues/10
[RFE-mbs]: https://pagure.io/fm-orchestrator/issue/1217

# modulemd_tools (python package)

Because `python3-libmodulemd` is not enough.

This package provides convenient functions for working with modulemd
YAML definitions. It is a place for sharing code among other tools
within this project. ~~It is also meant to be used as a dependency for
other tools, such as build-systems.~~ **It is not ready to be used by
other tools yet, be cautious.**

# bld2repo

Simple tool which will download modular build dependencies from a 
modular build in a koji instance and create a RPM repository out of it.

## usage

Provide a build id of modular build in koji and the cli tool will
download all the rpms tagged in a build tag of a modular rpm build.

```
$ bld2repo --build-id 1234
```

After the download is finished the tool will call createrepo_c on the
working directory, creating a rpm repository.

The defaults are set to the current fedora koji instance.
If you are using a different koji instance please adjust those
values through script arguments. For more information about script
arguments please run:

```
$ bld2repo -h
```