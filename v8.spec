# Hi Googlers! If you're looking in here for patches, nifty.
# You (and everyone else) are welcome to use any of my Chromium patches under the terms of the GPLv2 or later.
# You (and everyone else) are welcome to use any of my V8-specific patches under the terms of the BSD license.
# You (and everyone else) may NOT use my patches under any other terms.
# I hate to be a party-pooper here, but I really don't want to help Google make a proprietary browser.
# There are enough of those already.
# All copyrightable work in these spec files and patches is Copyright 2010 Tom Callaway

# For the 1.2 branch, we use 0s here
# For 1.3+, we use the three digit versions
%global somajor 3
%global sominor 10
%global sobuild 6
%global sover %{somajor}.%{sominor}.%{sobuild}
%{!?python_sitelib: %global python_sitelib %(%{__python} \
    -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:       v8
Version:    %{somajor}.%{sominor}.%{sobuild}.0
%if 0%{?fedora} >= 17
Epoch:      1
%endif
Release:    1%{?dist}
Summary:    JavaScript Engine
Group:      System Environment/Libraries
License:    BSD
URL:        http://code.google.com/p/v8
# No tarballs, pulled from svn
# Checkout script is Source1
Source0:    v8.%{version}.tar.lzma
Source1:    v8-daily-tarball.sh
# Enable experimental i18n extension that chromium needs
Patch0:     v8-3.3.10-enable-experimental.patch
# Remove unnecessary shebangs
Patch3:     v8-2.5.9-shebangs.patch
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
ExclusiveArch:    %{ix86} x86_64 arm
BuildRequires:    scons, readline-devel, libicu-devel

%description
V8 is Google's open source JavaScript engine. V8 is written in C++ and is used 
in Google Chrome, the open source browser from Google. V8 implements ECMAScript 
as specified in ECMA-262, 3rd edition.

%package devel
Group:      Development/Libraries
Summary:    Development headers and libraries for v8
Requires:   %{name} = %{?epoch}:%{version}-%{release}

%description devel
Development headers and libraries for v8.

%prep
%setup -q -n %{name}
#patch0 -p1 -b .experimental
%patch3 -p1 -b .shebang

#sed -i '/break-iterator.cc/d' src/SConscript
#sed -i '/collator.cc/d' src/SConscript
sed -i '/extensions\/experimental\//d' src/SConscript

# -fno-strict-aliasing is needed with gcc 4.4 to get past some ugly code
PARSED_OPT_FLAGS=`echo \'$RPM_OPT_FLAGS -fPIC -fno-strict-aliasing -Wno-unused-parameter -Wno-unused-but-set-variable\'| sed "s/ /',/g" | sed "s/',/', '/g"`
sed -i "s|'-O3',|$PARSED_OPT_FLAGS,|g" SConstruct

# clear spurious executable bits
find . \( -name \*.cc -o -name \*.h -o -name \*.py \) -a -executable \
  |while read FILE ; do
    echo $FILE
    chmod -x $FILE
  done


%build
export GCC_VERSION="46"
export COMPRESSION="off"
scons library=shared snapshots=on verbose=on \
%ifarch x86_64
arch=x64 \
%endif
visibility=default \
env=CCFLAGS:"-fPIC" \
%{?_smp_mflags}

%if 0%{?fedora} > 15
export ICU_LINK_FLAGS=`pkg-config --libs-only-l icu-i18n`
%else
export ICU_LINK_FLAGS=`pkg-config --libs-only-l icu`
%endif

# When will people learn to create versioned shared libraries by default?
# first, lets get rid of the old .so file
rm -rf libv8.so libv8preparser.so
# Now, lets make it right.

g++ $RPM_OPT_FLAGS -fPIC -o libv8preparser.so.%{sover} -shared -Wl,-soname,libv8preparser.so.%{somajor} \
        obj/release/allocation.os \
        obj/release/preparse-data.os \
        obj/release/preparser-api.os \
        obj/release/preparser.os \
        obj/release/token.os \
        obj/release/unicode.os
 
# "obj/release/preparser-api.os" should not be included in the libv8.so file.
export RELEASE_BUILD_OBJS=`echo obj/release/*.os | sed 's|obj/release/preparser-api.os||g'`

%ifarch arm
g++ $RPM_OPT_FLAGS -fPIC -o libv8.so.%{sover} -shared -Wl,-soname,libv8.so.%{somajor} $RELEASE_BUILD_OBJS obj/release/extensions/*.os obj/release/arm/*.os $ICU_LINK_FLAGS
%endif
%ifarch %{ix86}
g++ $RPM_OPT_FLAGS -fPIC -o libv8.so.%{sover} -shared -Wl,-soname,libv8.so.%{somajor} $RELEASE_BUILD_OBJS obj/release/extensions/*.os obj/release/ia32/*.os $ICU_LINK_FLAGS
%endif
%ifarch x86_64
g++ $RPM_OPT_FLAGS -fPIC -o libv8.so.%{sover} -shared -Wl,-soname,libv8.so.%{somajor} $RELEASE_BUILD_OBJS obj/release/extensions/*.os obj/release/x64/*.os $ICU_LINK_FLAGS
%endif

# We need to do this so d8 can link against it.
ln -sf libv8.so.%{sover} libv8.so
ln -sf libv8preparser.so.%{sover} libv8preparser.so

# This will fail to link d8 because it doesn't use the icu libs.
scons d8 \
%ifarch x86_64
arch=x64 \
%endif
library=shared snapshots=on console=readline visibility=default || :

# Sigh. I f*****g hate scons.
rm -rf d8

g++ $RPM_OPT_FLAGS -o d8 obj/release/d8.os -lpthread -lreadline -lpthread -L. -lv8 $ICU_LINK_FLAGS

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_includedir}
mkdir -p %{buildroot}%{_libdir}
install -p include/*.h %{buildroot}%{_includedir}
install -p libv8.so.%{sover} %{buildroot}%{_libdir}
install -p libv8preparser.so.%{sover} %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_bindir}
install -p -m0755 d8 %{buildroot}%{_bindir}

pushd %{buildroot}%{_libdir}
ln -sf libv8.so.%{sover} libv8.so
ln -sf libv8.so.%{sover} libv8.so.%{somajor}
ln -sf libv8.so.%{sover} libv8.so.%{somajor}.%{sominor}
ln -sf libv8preparser.so.%{sover} libv8preparser.so
ln -sf libv8preparser.so.%{sover} libv8preparser.so.%{somajor}
ln -sf libv8preparser.so.%{sover} libv8preparser.so.%{somajor}.%{sominor}
popd

chmod -x %{buildroot}%{_includedir}/v8*.h

mkdir -p %{buildroot}%{_includedir}/v8/extensions/experimental/
install -p src/extensions/*.h %{buildroot}%{_includedir}/v8/extensions/

chmod -x %{buildroot}%{_includedir}/v8/extensions/*.h

# install Python JS minifier scripts for nodejs
install -d %{buildroot}%{python_sitelib}
install -p -m0744 tools/jsmin.py %{buildroot}%{python_sitelib}/
chmod -R -x %{buildroot}%{python_sitelib}/*.py*

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
%{_includedir}/*.h
%{_includedir}/v8/extensions/
%{_libdir}/*.so
%{python_sitelib}/j*.py*

%changelog
* Fri Apr 27 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.10.6.0-1.R
- update to 3.10.6.0

* Thu Apr 26 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.10.5.0-1.R
- update to 3.10.5.0

* Thu Apr 19 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.10.2.1-1.R
- update to 3.10.2.1

* Sun Apr  8 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.10.0.5-1
- update to 3.10.0.5

* Thu Mar 29 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.24.1-2
- bump epoch for fedora >= 17

* Wed Mar 28 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.24.1-1
- update to 3.9.24.1

* Thu Mar 15 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.19.0-1
- update to 3.9.19.0

* Wed Mar  7 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.13.0-2
- update build options

* Wed Mar  7 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.13.0-1.R
- update to 3.9.13.0

* Fri Feb 24 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.7.0-2.R
- sync spec with fedora one

* Wed Feb 22 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.7.0-1.R                                                                                                     
- update to 3.9.7.0                                                                                                                                                           
                                                                                                                                                                              
* Mon Feb 20 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.1.0-2.R                                                                                                     
- ugly Provides hack                                                                                                                                                          
                                                                                                                                                                              
* Sat Feb 18 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.9.1.0-1.R                                                                                                     
- initial build for EL6 from openSUSE
