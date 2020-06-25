# dir2module

Recursively read RPMs from DIR or read them from specified pkglist.
If any RPM is missing on unreadable, error out.
Populate artifacts/rpms with RPM NEVRAs (sorted, deduplicated)
Populate license/content with list of RPM licenses (sorted, deduplicated)

Write N:S:V:C:A.modulemd.yaml in the current directory.
Make sure the yaml is in modulemd v2 format.

https://bugzilla.redhat.com/show_bug.cgi?id=1801747#c7
