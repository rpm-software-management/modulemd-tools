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
$ modulemd-generate-macros.py foo:devel:123:f32:x86_64.modulemd.yaml
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
