%global or_tag    latest-20260319
%global or_arch   linux64_gf

Name:           openradioss
Version:        20260319
Release:        1%{?dist}
Summary:        Open-source explicit finite element analysis solver

License:        AGPL-3.0-only
URL:            https://openradioss.org
Source0:        https://github.com/OpenRadioss/OpenRadioss/archive/refs/tags/%{or_tag}.tar.gz

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  gcc-gfortran >= 11
BuildRequires:  cmake >= 2.8
BuildRequires:  make
BuildRequires:  perl
BuildRequires:  python3
BuildRequires:  python3-devel
BuildRequires:  libasan
BuildRequires:  libubsan
BuildRequires:  openmpi-devel
# environment-modules 提供 modulecmd，openmpi-devel 在 Fedora 上依赖它来激活环境
BuildRequires:  environment-modules

Requires:       python3

%description
OpenRadioss is a high-performance explicit finite element solver widely
used for crash simulation, impact dynamics, and metal forming.

This package provides two components built with GFortran:
  - Starter (starter_%{or_arch}): model pre-processing
  - Engine (engine_%{or_arch}): time-domain solver (SMP)


%package openmpi
Summary:        OpenRadioss Engine built with OpenMPI support
Requires:       openmpi
Requires:       %{name} = %{version}-%{release}

%description openmpi
OpenRadioss Engine compiled with OpenMPI support for distributed-memory
parallel runs (engine_%{or_arch}_ompi).


%package doc
Summary:        OpenRadioss documentation
BuildArch:      noarch

%description doc
Documentation, contributing guide and license for OpenRadioss.


# ------------------------------------------------------------
%prep
%autosetup -n OpenRadioss-%{or_tag}


# ------------------------------------------------------------
%build
%global build_jobs %{?_smp_build_ncpus}%{!?_smp_build_ncpus:1}

# -fno-lto: 禁用 LTO，避免 LTO + OpenMP 导致的 TLS mismatch 链接错误
%global or_addflag -addflag="-fno-lto"

# --- Starter ---
pushd starter
  chmod +x build_script.sh
  ./build_script.sh \
      -arch=%{or_arch} \
      -release \
      %{or_addflag} \
      -nt=%{build_jobs}
popd

# --- Engine (SMP) ---
pushd engine
  chmod +x build_script.sh
  ./build_script.sh \
      -arch=%{or_arch} \
      -release \
      %{or_addflag} \
      -nt=%{build_jobs}
popd

# --- Engine (OpenMPI) ---
# Fedora 的 openmpi-devel 通过 Environment Modules 管理，
# mpif.h 实际路径需要在运行时 find 确定，不能硬编码。
# 用 find 找到 mpif.h 所在目录，再用 dirname 找 lib 目录。
OMPI_INC=$(find %{_libdir}/openmpi %{_includedir}/openmpi* \
               -name "mpif.h" -print -quit 2>/dev/null | xargs dirname)
OMPI_LIB=$(dirname ${OMPI_INC})/lib
# 如果 lib 不存在则回退到 openmpi lib 目录
[ -d "${OMPI_LIB}" ] || OMPI_LIB=%{_libdir}/openmpi/lib

echo "OpenMPI include dir: ${OMPI_INC}"
echo "OpenMPI lib dir:     ${OMPI_LIB}"

pushd engine
  ./build_script.sh \
      -arch=%{or_arch} \
      -mpi=ompi \
      -mpi-include=${OMPI_INC} \
      -mpi-libdir=${OMPI_LIB} \
      -release \
      %{or_addflag} \
      -nt=%{build_jobs}
popd


# ------------------------------------------------------------
%install
install -Dpm 0755 exec/starter_%{or_arch}      %{buildroot}%{_bindir}/starter_%{or_arch}
install -Dpm 0755 exec/engine_%{or_arch}       %{buildroot}%{_bindir}/engine_%{or_arch}
install -Dpm 0755 exec/engine_%{or_arch}_ompi  %{buildroot}%{_bindir}/engine_%{or_arch}_ompi

install -Dpm 0644 README.md       %{buildroot}%{_docdir}/%{name}/README.md
install -Dpm 0644 LICENSE.md      %{buildroot}%{_docdir}/%{name}/LICENSE.md
install -Dpm 0644 CONTRIBUTING.md %{buildroot}%{_docdir}/%{name}/CONTRIBUTING.md



# ------------------------------------------------------------
%files
%license LICENSE.md
%{_bindir}/starter_%{or_arch}
%{_bindir}/engine_%{or_arch}

%files openmpi
%{_bindir}/engine_%{or_arch}_ompi

%files doc
%{_docdir}/%{name}/


# ------------------------------------------------------------
%changelog
* Thu Mar 27 2025 Packager <packager@example.com> - 20260319-1
- Fix OpenMPI include/lib: dynamically detect paths via find at build time
- Add -fno-lto to fix TLS mismatch linker error
- Drop -static-link, use dynamic linking
- Add python3-devel to fix cpp_python_funct.cpp compilation
- Initial Copr packaging using upstream release tarball latest-20260319
