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