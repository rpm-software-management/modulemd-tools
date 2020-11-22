Name: modulemd-tools
Version: 0.5
Release: 1%{?dist}
Summary: Collection of tools for parsing and generating modulemd YAML files
License: MIT
BuildArch: noarch

URL: https://github.com/rpm-software-management/modulemd-tools
Source0: https://github.com/rpm-software-management/modulemd-tools/archive/%{version}/%{name}-%{version}.tar.gz

BuildRequires: libmodulemd >= 2
BuildRequires: createrepo_c
BuildRequires: createrepo_c
BuildRequires: argparse-manpage
BuildRequires: python3-setuptools
BuildRequires: python3-click
BuildRequires: python3-click-man
BuildRequires: python3-dnf
BuildRequires: python3-hawkey
BuildRequires: python3-createrepo_c
BuildRequires: python3-pyyaml
BuildRequires: python3-parameterized

Requires: libmodulemd >= 2
Requires: createrepo_c
Requires: python3-click
Requires: python3-dnf
Requires: python3-hawkey
Requires: python3-createrepo_c
Requires: python3-pyyaml


%description
Tools provided by this package:

repo2module - Takes a YUM repository on its input and creates modules.yaml
    containing YAML module definitions generated for each package.

dir2module - Generates a module YAML definition based on essential module
    information provided via command-line parameters. The packages provided by
    the module are found in a specified directory or a text file containing
    their list.

createrepo_mod - A small wrapper around createrepo_c and modifyrepo_c to provide
    an easy tool for generating module repositories.

modulemd-merge - Merge several modules.yaml files into one. This is useful for
    example if you have several yum repositories and want to merge them into one.

modulemd-generate-macros - Generate module-build-macros SRPM package, which is
    a central piece for building modules. It should be present in the buildroot
    before any other module packages are submitted to be built.


%prep
%setup -q


%build
cd repo2module
%py3_build
cd ..
./man/generate-manpages.sh


%install
cd repo2module
%py3_install
cd ..

cp dir2module/dir2module.py %{buildroot}%{_bindir}/dir2module
cp createrepo_mod/createrepo_mod.py %{buildroot}%{_bindir}/createrepo_mod
cp modulemd-merge/modulemd-merge.py %{buildroot}%{_bindir}/modulemd-merge
cp modulemd-generate-macros/modulemd-generate-macros.py \
    %{buildroot}%{_bindir}/modulemd-generate-macros

cp -r modulemd_tools/modulemd_tools %{buildroot}%{python3_sitelib}/modulemd_tools

install -d %{buildroot}%{_mandir}/man1
cp man/*.1 %{buildroot}%{_mandir}/man1/


%check
%{python3} repo2module/setup.py test
cd modulemd_tools
%{python3} -m unittest


%files
%doc README.md
%license LICENSE
%{python3_sitelib}/repo2module
%{python3_sitelib}/repo2module-*.egg-info/
%{_bindir}/repo2module
%{_bindir}/dir2module
%{_bindir}/createrepo_mod
%{_bindir}/modulemd-merge
%{_bindir}/modulemd-generate-macros
%{python3_sitelib}/modulemd_tools

%{_mandir}/man1/repo2module.1*
%{_mandir}/man1/dir2module.1*
%{_mandir}/man1/createrepo_mod.1*
%{_mandir}/man1/modulemd-merge.1*
%{_mandir}/man1/modulemd-generate-macros.1.*


%changelog
* Thu Nov 05 2020 Jakub Kadlcik <frostyx@email.cz> 0.5-1
- Release for epel8 as well (frostyx@email.cz)
- Require createrepo_c for the createrepo_mod package (frostyx@email.cz)
- modulemd-merge: improve README.md file (frostyx@email.cz)
- repo2module: improve README.md file (frostyx@email.cz)
- dir2module: improve README.md file (frostyx@email.cz)
- Improve README.md file (frostyx@email.cz)
- createrepo_mod: improve README.md file (frostyx@email.cz)
- Loosen the python3-libmodulemd dependency to just libmodulemd
  (frostyx@email.cz)
- createrepo_mod: use just createrepo_c if it has built-in module support
  (frostyx@email.cz)
- Explicitly depend on python3-setuptools (frostyx@email.cz)
- createrepo_mod: dump modules.yaml into the correct directory
  (frostyx@email.cz)

* Mon Aug 10 2020 Jakub Kadlcik <frostyx@email.cz> 0.4-1
- createrepo_mod: support also non-module repositories (frostyx@email.cz)

* Wed Jul 29 2020 Jakub Kadlcik <frostyx@email.cz> 0.3-1
- Add createrepo_mod and modulemd-merge scripts

* Sun Jul 26 2020 Jakub Kadlčík <jkadlcik@redhat.com> - 0.2-1
- Add createrepo_mod tool
- Add modulemd-merge tool
- Drop Source1, it is not needed anymore

* Tue Jun 09 2020 Jakub Kadlčík <jkadlcik@redhat.com> - 0.1-1
- Initial package
