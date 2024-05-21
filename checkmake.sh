#!/usr/bin/bash


TARBALL=$1
TIME=`date +%s`
DIR="tmp_$TIME"

usage () {
    echo "usage: check_tarball.sh TARBALL"
}


if [ -z "$TARBALL" ]; then
    usage
    exit 1
fi

mkdir $DIR

if [ $? -ne 0 ]; then
    echo "Could not create temp directory $DIR to expand tarball into"
    exit 1
fi


tar zxvf $TARBALL -C $DIR

if [ $? -ne 0 ]; then
    echo "Could not expand tarball into temp directory"
    rm -rf $DIR
    exit 1
fi

cd $DIR
make

if [ $? -ne 0 ]; then
    echo
    echo "Make failed. Resolve the issues and recheck"
    echo "Temp directory $DIR preserved for debugging"
    exit 1
fi

echo
echo "Tarball expands and make succeeds."
echo "Removing temp directory."

cd ..
rm -rf $DIR
