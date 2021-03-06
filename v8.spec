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
%global sominor 11
%global sobuild 10
%global sover %{somajor}.%{sominor}.%{sobuild}
%{!?python_sitelib: %global python_sitelib %(%{__python} \
    -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:       v8
Version:    %{somajor}.%{sominor}.%{sobuild}.6
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
# Remove unnecessary shebangs
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
* Tue Jun 19 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.11.10.6-1.R
- update to 3.11.10.6
- Implemented heap profiler memory usage reporting.
- Preserved error message during finally block in try..finally.
  (Chromium issue 129171)
- Fixed EnsureCanContainElements to properly handle double values.
  (issue 2170)
- Improved heuristics to keep objects in fast mode with inherited
  constructors.
- Performance and stability improvements on all platforms.
- Implemented ES5-conformant semantics for inherited setters and 
  read-only properties. Currently behind --es5_readonly flag, 
  because it breaks WebKit bindings.
- Exposed last seen heap object id via v8 public api.

* Fri Jun  8 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.11.8.0-1.R
- update to 3.11.8.0
- drop patch
- Avoid overdeep recursion in regexp where a guarded expression 
  with a minimum repetition count is inside another quantifier.
  (Chromium issue 129926)
- Fixed missing write barrier in store field stub.
  (issues 2143, 1465, Chromium issue 129355)
- Proxies: Fixed receiver for setters inherited from proxies.
- Proxies: Fixed ToStringArray function so that it does not 
  reject some keys. (issue 1543)
- Get better function names in stack traces.
- Fixed RegExp.prototype.toString for incompatible receivers
  (issue 1981).
- Some cleanup to common.gypi. This fixes some host/target 
  combinations that weren't working in the Make build on Mac.
- Handle EINTR in socket functions and continue incomplete sends.
  (issue 2098)
- Fixed python deprecations.  (issue 1391)
- Made socket send and receive more robust and return 0 on 
  failure.  (Chromium issue 15719)
- Fixed GCC 4.7 (C++11) compilation.  (issue 2136)
- Set '-m32' option for host and target platforms
- Performance and stability improvements on all platforms.

* Fri May 25 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.11.3.0-1.R
- update to 3.11.3.0
- Disable optimization for functions that have scopes that cannot
  be reconstructed from the context chain. (issue 2071)
- Define V8_EXPORT to nothing for clients of v8. 
  (Chromium issue 90078)
- Correctly check for native error objects. (Chromium issue 2138)
- Implement map collection for incremental marking. (issue 1465)
- Added a readbuffer function to d8 that reads a file into an 
  ArrayBuffer.
- Fix freebsd build. (V8 issue 2126)
- Fixed compose-discard crasher from r11524 (issue 2123).
- Activated new global semantics by default. Global variables can
  now shadow properties of the global object (ES5.1 erratum).
- Properly set ElementsKind of empty FAST_DOUBLE_ELEMENTS arrays when
  transitioning (Chromium issue 117409).
- Made Error.prototype.name writable again, as required by the spec and
  the web (Chromium issue 69187).
- Implemented map collection with incremental marking (issue 1465).
- Regexp: Fixed overflow in min-match-length calculation
  (Chromium issue 126412).
- Fixed crash bug in VisitChoice (Chromium issue 126272).
- Fixed unsigned-Smi check in MappedArgumentsLookup
  (Chromium issue 126414).
- Fixed LiveEdit for function with no locals (issue 825).
- Fixed register clobbering in LoadIC for interceptors
  (Chromium issue 125988).
- Implemented clearing of CompareICs (issue 2102).
- Performance and stability improvements on all platforms.

* Fri May 11 2012 Arkady L. Shane <ashejn@russianfedora.ru> - 3.10.8.4-1.R
- update to 3.10.8.4
- drop old patch

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
