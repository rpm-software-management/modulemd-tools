Name: modulemd-tools
Version: 0.3
Release: 1%{?dist}
Summary: Collection of tools for parsing and generating modulemd YAML files
License: MIT
BuildArch: noarch

URL: https://github.com/rpm-software-management/modulemd-tools
Source0: https://github.com/rpm-software-management/modulemd-tools/archive/%{version}/%{name}-%{version}.tar.gz

BuildRequires: python3-devel
BuildRequires: python3-click
BuildRequires: python3-dnf
BuildRequires: python3-libmodulemd
BuildRequires: python3-hawkey
BuildRequires: python3-createrepo_c

Requires: python3-click
Requires: python3-dnf
Requires: python3-libmodulemd
Requires: python3-hawkey
Requires: python3-createrepo_c


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


%prep
%setup -q


%build
cd repo2module
%py3_build


%install
cd repo2module
%py3_install
cd ..

cp dir2module/dir2module.py %{buildroot}%{_bindir}/dir2module
cp createrepo_mod/createrepo_mod.py %{buildroot}%{_bindir}/createrepo_mod
cp modulemd-merge/modulemd-merge.py %{buildroot}%{_bindir}/modulemd-merge


%check
%{python3} repo2module/setup.py test


%files
%doc README.md
%license LICENSE
%{python3_sitelib}/repo2module
%{python3_sitelib}/repo2module-*.egg-info/
%{_bindir}/repo2module
%{_bindir}/dir2module
%{_bindir}/createrepo_mod
%{_bindir}/modulemd-merge


%changelog
* Wed Jul 29 2020 Jakub Kadlcik <frostyx@email.cz> 0.3-1
- Add createrepo_mod and modulemd-merge scripts

* Sun Jul 26 2020 Jakub Kadlčík <jkadlcik@redhat.com> - 0.2-1
- Add createrepo_mod tool
- Add modulemd-merge tool
- Drop Source1, it is not needed anymore

* Tue Jun 09 2020 Jakub Kadlčík <jkadlcik@redhat.com> - 0.1-1
- Initial package
