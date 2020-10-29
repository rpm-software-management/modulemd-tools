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
