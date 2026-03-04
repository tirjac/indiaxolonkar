#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# main

if [ $# -lt 1 ] ; then
	echo "Usage: $0 <image_path> [objective] [category] [comments]"
	exit 1
fi

IMG="$1"
OBJ=${2:-sales}
CAT=${3:-Others}
COM=${4:-""}

python src/send_job.py "${IMG}" --objective "${OBJ}" --category "${CAT}" --comments "${COM}"
