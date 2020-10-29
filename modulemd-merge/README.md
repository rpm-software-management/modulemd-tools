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
