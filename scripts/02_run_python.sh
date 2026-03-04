#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ $# -lt 1 ] ; then exit 1 ; fi

# main
python "$@"
