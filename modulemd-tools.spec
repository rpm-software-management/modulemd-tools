Name: modulemd-tools
Version: 0.13
Release: 1%{?dist}
Summary: Collection of tools for modular (in terms of Fedora Modularity origin) content creators
License: MIT
BuildArch: noarch

URL: https://github.com/rpm-software-management/modulemd-tools
Source0: https://github.com/rpm-software-management/modulemd-tools/archive/%{version}/%{name}-%{version}.tar.gz

BuildRequires: createrepo_c
BuildRequires: argparse-manpage
BuildRequires: python3-devel
BuildRequires: python3-pip
BuildRequires: python3-setuptools
BuildRequires: python3-wheel
BuildRequires: python3-libmodulemd >= 2.9.3
BuildRequires: python3-dnf
BuildRequires: python3-hawkey
BuildRequires: python3-createrepo_c
BuildRequires: python3-pyyaml
BuildRequires: python3-pytest
BuildRequires: python3-koji

Requires: createrepo_c
Requires: python3-dnf
Requires: python3-hawkey
Requires: python3-createrepo_c
Requires: python3-pyyaml
Requires: python3-libmodulemd >= 2.9.3
Requires: python3-koji


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

modulemd-add-platform - Add a new context configuration for a new platform
    into a modulemd-packager file.

modulemd-merge - Merge several modules.yaml files into one. This is useful for
    example if you have several yum repositories and want to merge them into one.

modulemd-generate-macros - Generate module-build-macros SRPM package, which is
    a central piece for building modules. It should be present in the buildroot
    before any other module packages are submitted to be built.

bld2repo - Simple tool for dowloading build required RPMs of a modular build from koji.


%prep
%setup -q


%build
%py3_build

PYTHONPATH=: ./man/generate-manpages.sh


%install
%py3_install

install -d %{buildroot}%{_mandir}/man1
cp man/*.1 %{buildroot}%{_mandir}/man1/


%check
%{python3} -m pytest -vv


%files
%doc README.md
%license LICENSE

%{python3_sitelib}/modulemd_tools
%{python3_sitelib}/modulemd_tools-*.egg-info/

%{_bindir}/repo2module
%{_bindir}/dir2module
%{_bindir}/createrepo_mod
%{_bindir}/modulemd-add-platform
%{_bindir}/modulemd-merge
%{_bindir}/modulemd-generate-macros
%{_bindir}/bld2repo

%{_mandir}/man1/repo2module.1*
%{_mandir}/man1/dir2module.1*
%{_mandir}/man1/createrepo_mod.1*
%{_mandir}/man1/modulemd-add-platform.1*
%{_mandir}/man1/modulemd-merge.1*
%{_mandir}/man1/modulemd-generate-macros.1.*
%{_mandir}/man1/bld2repo.1.*


%changelog
* Wed Feb 23 2022 Jakub Kadlcik <frostyx@email.cz> 0.13-1
- modulemd_add_platform: don't use pyproject macros (frostyx@email.cz)
- createrepo_mod: fix failing test because of modulemd-merge (frostyx@email.cz)
- Add modulemd_add_platform tool (ppisar@redhat.com)
- Fix bld2repo issue causing possibly missed dependencies (fvalder@redhat.com)

* Wed Feb 09 2022 Petr Pisar <ppisar@redhat.com> - 0.12-1
- Add modulemd-add-platform tool

* Mon Aug 23 2021 Jakub Kadlcik <frostyx@email.cz> 0.11-1
- modulemd_tools: compatibility for upgrade_ext on EPEL8 (frostyx@email.cz)
- modulemd_tools: compatibility for read_packager_string on EPEL8
  (frostyx@email.cz)
- dir2module: generate also profiles and modulemd-defaults file
  (frostyx@email.cz)
- modulemd_tools: use upgrade_ext instead of upgrade (frostyx@email.cz)
- modulemd_tools: use read_packager_string instead of read_string
  (frostyx@email.cz)
- Add installation instructions (frostyx@email.cz)
- bld2repo: do not create empty repos when --result-dir is used
  (kdudka@redhat.com)
- bld2repo: print status in a more intuitive format (kdudka@redhat.com)
- tito: stop releasing for Fedora 32 (frostyx@email.cz)

* Mon Jun 14 2021 Jakub Kadlcik <frostyx@email.cz> 0.10-1
- Added bld2repo (mcurlej@redhat.com)

* Fri Apr 09 2021 Jakub Kadlcik <frostyx@email.cz> 0.9-1
- repo2module: drop python-click dependency (frostyx@email.cz)

* Tue Apr 06 2021 Jakub Kadlcik <frostyx@email.cz> 0.8-1
- modulemd_tools: drop python3-parameterized dependency (frostyx@email.cz)
- Package modulemd_tools helper lib (fvalder@redhat.com)
- Add modulemd-merge tests (fvalder@redhat.com)
- Add createrepo_mod tests (fvalder@redhat.com)
- Replace master in fedora releaser to rawhide (frostyx@email.cz)

* Tue Feb 09 2021 Jakub Kadlcik <frostyx@email.cz> 0.7-1
- Generate manpages on the fly
- Automated test builds incl. Docker/Travis
- Fix PEP8 in all tools
- modulemd_tools: temporarily skip some tests on EPEL8 or Fedora
- Drop libmodulemd dependency in favor of python3-libmodulemd

* Sun Nov 22 2020 Jakub Kadlcik <frostyx@email.cz> 0.6-1
- Generate manpages for all tools in this repository 
- modulemd-generate-macros: add a tool for generating module-build-macros
- modulemd_tools: add the first pieces of a python library (for internal usage only)

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
