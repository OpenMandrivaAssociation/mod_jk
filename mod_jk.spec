%define apxs            %{_sbindir}/apxs
%define aprconf         %{_bindir}/apr-1-config
%define aplibdir        %(%{apxs} -q LIBEXECDIR 2>/dev/null)
%define apconfdir       %(%{apxs} -q SYSCONFDIR 2>/dev/null)
%define aprincludes     %(%{aprconf} --includes 2>/dev/null)
%define aplogdir        logs
%define section         free
%define build_free      1

Name:           mod_jk
Version:        1.2.30
Release:        %mkrel 1
Epoch:          0
Summary:        Tomcat mod_jk connector for Apache
#Vendor:        JPackage Project
#Distribution:  JPackage
License:        Apache License
Group:          Development/Java
URL:            https://tomcat.apache.org/
Source0:        http://www.apache.org/dist/tomcat/tomcat-connectors/jk/source/tomcat-connectors-%{version}-src.tar.gz
Source1:        http://www.apache.org/dist/tomcat/tomcat-connectors/jk/source/tomcat-connectors-%{version}-src.tar.gz.asc
Source2:        http://www.apache.org/dist/tomcat/tomcat-connectors/jk/source/tomcat-connectors-%{version}-src.tar.gz.md5
Patch0:         mod_jk-no-jvm1.patch
Patch1:		mod_jk-aplogerror.patch
Patch2:		tomcat-connectors-1.2.30-mod_jk.conf-use-separate-cache-dir.patch
Patch3:		tomcat-connectors-1.2.30-workers.properties-only-use-default-system-tomcat-node.patch
BuildRequires:  ant
BuildRequires:  ant-trax
BuildRequires:  apache-devel
BuildRequires:  java-devel
BuildRequires:  java-rpmbuild >= 0:1.5.38
BuildRequires:  libtool
BuildRequires:  perl
BuildRequires:  xalan-j2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root

%description
Tomcat mod_jk connector for Apache.

%if %with apache1
%package        ap13
Summary:        Tomcat mod_jk connector for Apache 1.3.x
Group:          Development/Java
Obsoletes:      mod_jk < %{epoch}:%{version}-%{release}
Provides:       mod_jk = %{epoch}:%{version}-%{release}
Obsoletes:      tomcat-mod < %{epoch}:%{version}-%{release}

%description    ap13
Tomcat mod_jk connector for Apache 1.3.x.
%endif

%package        ap20
Summary:        Tomcat mod_jk connector for Apache 2.0.x
Group:          Development/Java
Obsoletes:      mod_jk < %{epoch}:%{version}-%{release}
Provides:       mod_jk = %{epoch}:%{version}-%{release}
Obsoletes:      tomcat-mod < %{epoch}:%{version}-%{release}

%description    ap20
Tomcat mod_jk connector for Apache 2.0.x.

%package        manual
Summary:        Tomcat mod_jk connector manual
Group:          Development/Java

%description    manual
Tomcat mod_jk connector manual.

%package        tools
Group:          Development/Java
Summary:        Analysis and report tools for mod_jk

%description    tools
Miscellaneous mod_jk analysis and report tools.

%prep
%setup -q -n tomcat-connectors-%{version}-src
%if %{build_free}
%patch0 -p1
%endif
%patch1 -p0
%patch2 -p1 -b .cache_dir~
%patch3 -p1 -b .multi_nodes
(cd native && %{__libtoolize} --copy --force)

%{__perl} -pi -e 's|/usr/local/bin\b|%{_bindir}|' tools/reports/*.pl
%{__perl} -pi -e 's|^(APXSCPPFLAGS=.*)$|$1 %{aprincludes}|' \
  native/common/Makefile.in

%build
cd native

%{configure2_5x} \
  --with-apxs=%{apxs} \
  --with-java-home=%{java_home} \
  --with-java-platform=2 \
  --enable-jni \
%if %with apache1
  --enable-EAPI
%endif

# See <http://marc.theaimsgroup.com/?l=tomcat-dev&m=105600821630990>
%if %without apache1
export LIBTOOL=`%{apxs} -q LIBTOOL 2>/dev/null`
# Handle old apxs (without -q LIBTOOL), eg Red Hat 8.0 and 9.
if test -z "$LIBTOOL"; then
  LIBTOOL=%{__libtool}
fi
%{make} \
  LIBTOOL="$LIBTOOL" \
  EXTRA_CFLAGS="%{optflags}" \
  EXTRA_CPPFLAGS="%{aprincludes}"
%else
%{make} EXTRA_CFLAGS="$RPM_OPT_FLAGS"
%endif
cd ..

cd xdocs ; CLASSPATH=$(%{_bindir}/build-classpath xalan-j2-serializer) %{ant} ; cd ..

%install
%{__rm} -rf %{buildroot}
%{__mkdir_p} %{buildroot}%{aplibdir}
%{__install} -pm 0755 \
  native/jni/jk_jnicb.so %{buildroot}%{aplibdir}/jk_jnicb.so
%if %without apache1
%{__install} -pm 0755 \
  native/apache-2.0/mod_jk.so %{buildroot}%{aplibdir}/mod_jk.so
%else
%{__install} -pm 0755 \
  native/apache-1.3/mod_jk.so.0.0.0 %{buildroot}%{aplibdir}/mod_jk.so
%endif
%{__mkdir_p} %{buildroot}%{_bindir}
%{__install} -pm 0755 tools/reports/*.pl %{buildroot}%{_bindir}

%{__install} -m644 conf/workers.properties -D %{buildroot}%{_sysconfdir}/httpd/conf/workers.properties
%{__install} -m644 conf/httpd-jk.conf -D %{buildroot}%{_sysconfdir}/httpd/modules.d/30_mod_jk.conf
%{__mkdir_p} %{buildroot}/var/cache/httpd/mod_jk
touch %{buildroot}/var/cache/httpd/mod_jk/mod_jk.shm

%post ap20
service httpd condrestart

%postun ap20
service httpd condrestart

%clean
%{__rm} -rf %{buildroot}

%if %with apache1
%files ap13
%defattr(0644,root,root,0755)
%doc LICENSE NOTICE mod_jk.conf.sample workers.properties.sample
%doc native/BUILDING.txt native/CHANGES native/NEWS native/README.txt native/STATUS.txt native/TODO.txt
%defattr(-,root,root,-)
%{aplibdir}/*
%else
%files ap20
%defattr(0644,root,root,0755)
%doc LICENSE NOTICE conf/workers.properties.multi_nodes conf/workers.properties.minimal
%doc native/BUILDING.txt native/CHANGES native/NEWS native/README.txt native/STATUS.txt native/TODO.txt
%defattr(-,root,root,-)
%{aplibdir}/*
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/modules.d/*_mod_jk.conf
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/workers.properties
%attr(0700,apache,root) %dir /var/cache/httpd/mod_jk
%attr(0600,apache,root) %ghost /var/cache/httpd/mod_jk/mod_jk.shm
%endif

%files manual
%defattr(0644,root,root,0755)
%doc build/docs/*

%files tools
%defattr(0644,root,root,0755)
%doc tools/reports/README.txt
%attr(0755,root,root) %{_bindir}/*


