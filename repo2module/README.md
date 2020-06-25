# repo2module
## Prerequisites
### Packages
* [libmodulemd](https://github.com/fedora-modularity/libmodulemd)
* [libdnf](https://github.com/rpm-software-management/libdnf)
* [createrepo_c](https://github.com/rpm-software-management/createrepo_c)

To install on Fedora 28+, run:
```
dnf install python3-libmodulemd python3-libdnf python3-createrepo_c
```

### RPM Repo
You will need a yum repository (created with the `createrepo_c` tool)
containing exactly the set of RPMs that you want to include in the module.
These RPMs must have been built with the `ModularityLabel` header set to an
appropriate `N:S:V:C` value for the module.


## Installation
To install from source, just do `python3 setup.py install --user`. This will
put the `repo2module` tool in your `~/.local/bin` path.


## CLI Usage
Example:

`repo2module --module-name=testmodule --module-stream=stable ./testmodule modules.yaml`

This will generate most of the module metadata that you will need for this
repository to be treated as a module. You should examine the contents of
`modules.yaml` and modify it as appropriate.

Note: by this tool adds all packages in the repository to the `api` section and
the `common` profile. It will also generate a Defaults object setting this
`common` as the default profile for this stream. It will not set a default
stream, so you'll want to do this manually as appropriate.

## Inject the metadata
Once you've ensured that `modules.yaml` has the correct content, you can inject
it into the repodata with the command:
`modifyrepo_c --mdtype=modules modules.yaml ./testmodule/repodata`

Add that repo to your DNF/yum configuration and your content will be visible as
a module.
