# createrepo_mod

A small wrapper around `createrepo_c` and `modifyrepo_c` to provide an easy tool
for generating module repositories.

This is supposed to be only a temporary solution, in the future we would like to
have the modularity support implemented in `createrepo_c` itself. See

https://bugzilla.redhat.com/show_bug.cgi?id=1816753

This tool can be used as a drop-in replacement for `createrepo_c` with
one caveat. You need to specify `<directory>` before `[options]`.
Otherwise it works fine with both module and non-module repositories.

Please see the official Fedora Modularity documentation for the reference of how
module repositories should be created

https://docs.fedoraproject.org/en-US/modularity/hosting-modules/
