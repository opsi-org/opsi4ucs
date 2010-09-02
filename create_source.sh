#!/bin/bash

destdir=$1
cwd=$(pwd)
dir=$(dirname ${cwd}/$(dirname $0))
[ "$destdir" = "" ] && destdir=$cwd

packagename=$(head -n1 debian/changelog | cut -d' ' -f1)
version=$(head -n1 debian/changelog | cut -d'(' -f2 | cut -d')' -f1 | cut -d'-' -f1)
release=$(head -n1 debian/changelog | cut -d'(' -f2 | cut -d')' -f1 | cut -d'-' -f2)
tmpdir=/tmp/${packagename}-${version}

cd $dir
rm ${destdir}/${packagename}*.tar.gz  2>/dev/null || true
rm ${destdir}/${packagename}*.dsc     2>/dev/null || true

test -e $tmpdir && rm -rf $tmpdir
mkdir $tmpdir
cp -r 99opsi4ucs.inst conffiles files opsi-setup univention_baseconfig.py debian univention univention-install-baseconfig ${tmpdir}/
find ${tmpdir} -iname "*.pyc"   -exec rm "{}" \;
find ${tmpdir} -iname "*.marks" -exec rm "{}" \;
find ${tmpdir} -iname "*~"      -exec rm "{}" \;
find ${tmpdir} -iname "*.svn"   -exec rm -rf "{}" \; 2>/dev/null

cd ${tmpdir}/
dpkg-buildpackage -S
mv ${tmpdir}/../${packagename}_${version}-${release}.tar.gz $destdir/
mv ${tmpdir}/../${packagename}_${version}-${release}.dsc    $destdir/
rm -rf $tmpdir
echo "============================================================================================="
echo "source archive: ${destdir}/${packagename}_${version}-${release}.tar.gz"
echo "dsc file:       ${destdir}/${packagename}_${version}-${release}.dsc"
echo "============================================================================================="
cd $cwd

