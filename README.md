# modulemd-tools

Collection of tools for modular (in terms of Fedora Modularity origin) content creators


## Tools provided by this package

[>>> Detailed README about individual tools usage <<<](README-DETAILED.md)

### repo2module

**Author: Stephen Gallagher <<sgallagh@redhat.com>>**

Takes a YUM repository on its input and creates modules.yaml
containing YAML module definitions generated for each package.

For more information about `repo2module`, please see
[repo2module/README.md](repo2module/README.md)


### dir2module

**Author: Jakub Kadlcik <<frostyx@email.cz>>**

Generates a module YAML definition based on essential module
information provided via command-line parameters. The packages provided by
the module are found in a specified directory or a text file containing
their list.

For more information about `dir2module`, please see
[dir2module/README.md](dir2module/README.md)


### createrepo_mod

**Author: Jakub Kadlcik <<frostyx@email.cz>>**

A small wrapper around `createrepo_c` and `modifyrepo_c` to
provide an easy tool for generating module repositories.

For more information about `createrepo_mod`, please see
[createrepo_mod/README.md](createrepo_mod/README.md)


### modulemd-add-platform

**Author: Petr Pisar <<ppisar@redhat.com>>**

Add a context configuration for a new platform to a modulemd-packager-v3
document.

For more information about `modulemd-add-platform`, please see
[modulemd-add-platform/README.md](modulemd-add-platform/README.md)


### modulemd-merge

**Author: Gerd v. Egidy <<gerd.von.egidy@intra2net.com>>**

Merge several modules.yaml files into one.

For more information about `modulemd-merge`, please see
[modulemd-merge/README.md](modulemd-merge/README.md)


### modulemd-generate-macros

**Author: Jakub Kadlcik <<frostyx@email.cz>>**

Generate `module-build-macros` SRPM package, which is a central piece
for building modules. It should be present in the buildroot before any
other module packages are submitted to be built.

For more information about `modulemd-generate-macros`, please see
[modulemd-generate-macros/README.md](modulemd-generate-macros/README.md)


### modulemd_tools (python library)

**Author: Jakub Kadlcik <<frostyx@email.cz>>**

Provides convenient functions for working with modulemd
YAML definitions. It is a place for sharing code among other tools
within this project. ~~It is also meant to be used as a dependency for
other tools, such as build-systems.~~ **It is not ready to be used by
other tools yet, be cautious.**
[modulemd_tools/README.md](modulemd_tools/README.md)


### bld2repo

**Author: Martin Curlej <<mcurlej@redhat.com>>**

Simple tool for dowloading build required RPMs of a modular build from koji.

For more information about `bld2repo`, please see
[bld2repo/README.md](bld2repo/README.md)


## Installation instructions

The `modulemd-tools` package is available in the official Fedora
repositories, and RHEL 8.5 and higher. As such, it can be easily
installed with:

```
dnf install modulemd-tools
```

There is also a Copr repository providing up-to-date stable builds for
EPEL8. It is recommended to use this repository for installing
`modulemd-tools` on RHEL 8.4 and lower.

```
dnf copr enable frostyx/modulemd-tools-epel
dnf install modulemd-tools
```

If you prefer to install the latest stable package from this
repository, use

```
git clone https://github.com/rpm-software-management/modulemd-tools.git
cd modulemd-tools
sudo dnf builddep modulemd-tools.spec
tito build --rpm --install
```

Alternatively, if you want to build and install a package from the
latest commit, use

```
tito build --rpm --test --install
```


## Use cases

### Creating a module repository from a regular repository

Let's assume that we have a regular (meaning non-modular) repository.

```
$ ls
hello-2.8-1.fc32.x86_64.rpm  repodata
```

We might want to convert this repository to a modular repository, i.e. creating
a module providing current packages and then making the module available through
the repository. It is a two-step process. First, generate a modulemd YAML
providing all repository packages.

```
$ repo2module . \
    --module-name foo \
    --module-stream devel \
    --module-version 123 \
    --module-context f32
```

This command generates a `modules.yaml` file, you might want to open it in a
text editor and review its contents.

```
$ ls
hello-2.8-1.fc32.x86_64.rpm  modules.yaml  repodata
```

Once the `modules.yaml` fits your expectations (it shouldn't require any changes
for the tooling to work, you might want to fill in just some information for its
users), re-create the repository to provide the module. For that, use
`createrepo_mod`, or `createrepo_c` in the `0.16.1` version and above. They both
accept the same parameters.

```
$ createrepo_mod .
```

Optionally, check that the module metadata is available within the repository.

```
$ ls repodata/ |grep modules
c92f0efc3db47c5c8875665699781d001d9a78afdb49fab301b19d84968932f8-modules.yaml.gz
```


### Creating a module repository from a set of RPM packages

Let's start with just a normal directory containing one or many RPM files.

```
$ ls
hello-2.8-1.fc32.x86_64.rpm
```

We might want to create a module providing those packages and then make the
module available through a repository. It is a two-step process. First, generate
a modulemd YAML providing all packages in the directory.

```
$ dir2module foo:devel:123:f32:x86_64 -m "My example module" --dir .
```

You will most likely encounter the following error.
```
WARNING: RPM does not have `modularitylabel` header set: ./hello-2.8-1.fc32.x86_64.rpm
Error: All packages need to contain the `modularitylabel` header.
To suppress this constraint, use `--force` parameter
```

That's because module RPM packages should contain a `modularitylabel` header,
please see the [Modules – Fake it till you make it][modularity-label] blogpost
from [@sgallagher][sgallagher].

For the sake of simplicity, we won't deal with that and use `--force` parameter
to suppress the warning and generate the module YAML despite that.

```
$ ls
foo:devel:123:f32:x86_64.modulemd.yaml  hello-2.8-1.fc32.x86_64.rpm
```

You might want to review and edit the generated YAML file. Once it fits your
expectations (it shouldn't require any changes for the tooling to work, you
might want to fill in just some information for its users), create a Yum
repository from this directory. For that, use `createrepo_mod`, or
`createrepo_c` in the `0.16.1` version and above. They both accept the same
parameters.

```
$ createrepo_mod .
```

Optionally, check that the module metadata is available within the repository.

```
$ ls repodata/ |grep modules
14ff485b98924c8e97bba9b0c9e369283f15f3e30ffaf637186eb5e3f13fc178-modules.yaml.gz
```


### Installing module from a local repository

Let's assume that you have successfully created a modular repository as
described in the previous chapters and it is located at `/tmp/myrepo`. First, we
need to let Dnf know that exists. For that, create a
`/etc/yum.repos.d/myrepo.repo` file with following content.

```
[myrepo]
name=My local foo module
baseurl=file:///tmp/myrepo
gpgcheck=0
enabled=1
```

That is enough for the client to be able to work with the module. Check that Dnf
can find it.

```
$ dnf module info foo:devel
Name             : foo
Stream           : devel [d][a]
Version          : 123
Context          : f32
...
```

You should be able to install the module.

```
$ sudo dnf module install foo:devel
```

In this example case, the `foo:devel` module provides `hello` package. Let's
test that it was successfully installed.

```
$ hello
Hello, world!
```


### Merging two modulemd YAML files into one

Sometimes you might need to merge two modulemd YAML files. Such a task is done
e.g. internally in `createrepo_mod` and `createrepo_c` (`0.16.1` and
newer) when dumping `modules.yaml` file based on input modulemd YAML
files.

In the following example we have two input files -
`foo:devel:123:f32:x86_64.modulemd.yaml` and
`bar:stable:234:f32:x86_64.modulemd.yaml` and merging them into `modules.yaml`.

```
$ modulemd-merge -i \
    foo:devel:123:f32:x86_64.modulemd.yaml \
    bar:stable:234:f32:x86_64.modulemd.yaml \
    modules.yaml
```

We can quickly make sure the final YAML file contains both modules.

```
$ grep name modules.yaml -A2
  name: bar
  stream: stable
  version: 234
--
  name: foo
  stream: devel
  version: 123
```


### Building a module for the next distribution version

Modulemd YAML files in modulemd-packager format needs to list each supported
platform stream. When porting a module to the next distribution version it is
necessary to add a new `context configuration` matching the new platform.
`modulemd-add-platform` tool helps with it.

For instance, porting a `module.yaml` from Fedora 35 to Fedora 36 can be
achieved with:

```
$ modulemd-add-platform --old f35 --new f36 module.yaml
```


[modularity-label]: https://sgallagh.wordpress.com/2019/08/14/sausage-factory-modules-fake-it-till-you-make-it/
[sgallagher]: https://github.com/sgallagher
