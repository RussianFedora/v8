%global somajor `echo %{version} | cut -f1 -d'.'`
%global sominor `echo %{version} | cut -f2 -d'.'`
%global sobuild `echo %{version} | cut -f3 -d'.'`
%global sover %{somajor}.%{sominor}.%{sobuild}

Summary:        JavaScript Engine
Name:           v8
Version:        3.9.7.0
Release:        1%{?dist}.R

License:        BSD
Group:          System Environment/Libraries
Url:            http://code.google.com/p/v8
Source0:        http://download.rfremix.ru/storage/chromium/19.0.1046.0/%{name}.%{version}.tar.lzma
Patch0:         buildfix.diff
Patch1:         adjust-buildflags.diff
BuildRequires:  scons, readline-devel, libicu-devel, ncurses-devel, lzma
ExclusiveArch:  %{ix86} x86_64 arm
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%if 0%{?fedora} >= 16
%ifarch x86_64
Provides:       libv8preparser.so()(64bit)
%else
Provides:       libv8preparser.so
%endif
%endif

%description
V8 is Google's open source JavaScript engine. V8 is written in C++ and is used
in Google Chrome, the open source browser from Google. V8 implements ECMAScript
as specified in ECMA-262, 3rd edition.

%package devel

Summary:        Development headers and libraries for v8
Group:          Development/Libraries
Requires:       %{name} = %{version}-%{release}

%description devel
Development headers and libraries for v8.

%prep
rm -rf %{name}
lzma -cd %{SOURCE0} | tar xf -

%setup -D -T -n %{name}
%patch0 -p0
%patch1 -p0

%if 0%{?rhel} < 7
# -fno-strict-aliasing is needed with gcc 4.4 to get past some ugly code
PARSED_OPT_FLAGS=`echo \'%{optflags} \' | sed "s/ /',/g" | sed "s/',/', '/g"`
sed -i "s|'-O3',|$PARSED_OPT_FLAGS '-fno-strict-aliasing',|g" SConstruct
%endif

%build

scons -j3 library=shared snapshots=on visibility=default mode=release \
%ifarch x86_64
arch=x64 \
%endif
%ifarch arm
armeabi=hard vfp3=on \
%endif
env=CCFLAGS:"-fPIC"

# When will people learn to create versioned shared libraries by default?
# first, lets get rid of the old .so
rm -rf libv8.so
rm -rf libv8preparser.so
# Now, lets make it right.
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 17
g++ %{optflags} -fPIC -o libv8preparser.so.%{sover} -shared -Wl,-soname,libv8preparser.so.%{somajor} obj/release/allocation.os obj/release/bignum-dtoa.os obj/release/bignum.os obj/release/cached-powers.os obj/release/conversions.os obj/release/diy-fp.os obj/release/dtoa.os obj/release/fast-dtoa.os obj/release/fixed-dtoa.os obj/release/hashmap.os obj/release/preparse-data.os obj/release/preparser-api.os obj/release/preparser.os obj/release/scanner.os obj/release/strtod.os obj/release/token.os obj/release/unicode.os obj/release/utils.os -lpthread
%else
g++ %{optflags} -fPIC -o libv8preparser.so.%{sover} -shared -W1,-soname,libv8preparser.so.%{somajor} obj/release/allocation.os obj/release/bignum-dtoa.os obj/release/bignum.os obj/release/cached-powers.os obj/release/conversions.os obj/release/diy-fp.os obj/release/dtoa.os obj/release/fast-dtoa.os obj/release/fixed-dtoa.os obj/release/hashmap.os obj/release/preparse-data.os obj/release/preparser-api.os obj/release/preparser.os obj/release/scanner.os obj/release/strtod.os obj/release/token.os obj/release/unicode.os obj/release/utils.os -lpthread
rm obj/release/preparser-api.os
%endif
%ifarch arm
g++ %{optflags} -fPIC -o libv8.so.%{sover} -shared -Wl,-soname,libv8.so.%{somajor} obj/release/*.os obj/release/arm/*.os obj/release/extensions/*.os -lpthread
%endif
%ifarch %{ix86}
g++ %{optflags} -fPIC -o libv8.so.%{sover} -shared -Wl,-soname,libv8.so.%{somajor} obj/release/*.os obj/release/ia32/*.os obj/release/extensions/*.os -lpthread
%endif
%ifarch x86_64
g++ %{optflags} -fPIC -o libv8.so.%{sover} -shared -Wl,-soname,libv8.so.%{somajor} obj/release/*.os obj/release/x64/*.os obj/release/extensions/*.os -lpthread
%endif

# We need to do this so d8 can link against it.
ln -sf libv8.so.%{sover} libv8.so
ln -sf libv8preparser.so.%{sover} libv8preparser.so

scons d8 mode=release \
%ifarch x86_64
arch=x64 \
%endif
%ifarch arm
armeabi=hard vfp3=on \
%endif
library=shared snapshots=on console=readline visibility=default

# Sigh. I f*****g hate scons.
rm -rf d8

g++ %{optflags} -o d8 obj/release/d8.os -lv8 -lpthread -lreadline -L.

%install
#%if %suse_version > 1140
mkdir -p %{buildroot}%{_includedir}/v8/x64
#%else
mkdir -p %{buildroot}%{_includedir}
#%endif
mkdir -p %{buildroot}%{_libdir}
install -p include/*.h %{buildroot}%{_includedir}

#%if %suse_version > 1140
install -p src/*.h %{buildroot}%{_includedir}/v8
install -p src/x64/*.h %{buildroot}%{_includedir}/v8/x64
#%endif

install -p libv8.so.%{sover} %{buildroot}%{_libdir}
install -p libv8preparser.so.%{sover} %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_bindir}
install -p -m0755 d8 %{buildroot}%{_bindir}

cd %{buildroot}%{_libdir}
ln -sf libv8.so.%{sover} libv8.so
ln -sf libv8.so.%{sover} libv8.so.%{somajor}
ln -sf libv8.so.%{sover} libv8.so.%{somajor}.%{sominor}
ln -sf libv8preparser.so.%{sover} libv8preparser.so.%{somajor}.%{sominor}
ln -sf libv8preparser.so.%{sover} libv8preparser.so.%{somajor}
ln -sf libv8preparser.so.%{sover} libv8preparser.so

chmod -x %{buildroot}%{_includedir}/v8*.h

rm -rf %{buildroot}%{_datadir}/doc/libv8*

%clean
rm -rf %{buildroot}

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%defattr(-,root,root,-)
%doc AUTHORS ChangeLog LICENSE
%{_bindir}/d8
%{_libdir}/*.so.*

%files devel
%defattr(-,root,root,-)
%{_includedir}/*
%{_libdir}/*.so


%changelog
* Wed Feb 22 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.7.0-1.R
- update to 3.9.7.0

* Mon Feb 20 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.1.0-2.R
- ugly Provides hack

* Sat Feb 18 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.1.0-1.R
- initial build for EL6 from openSUSE
