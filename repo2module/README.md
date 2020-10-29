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
