# modulemd-tools

Collection of tools for parsing and generating modulemd YAML files

---

Tools provided by this package:

repo2module - Takes a YUM repository on its input and creates modules.yaml
    containing YAML module definitions generated for each package.

dir2module - Generates a module YAML definition based on essential module
    information provided via command-line parameters. The packages provided by
    the module are found in a specified directory or a text file containing
    their list.

createrepo_mod - A small wrapper around `createrepo_c` and `modifyrepo_c` to
    provide an easy tool for generating module repositories.

modulemd-merge - merge several modules.yaml files into one
