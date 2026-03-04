#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# main

if [ $# -ne 1 ] ; then
	echo "Usage: $0 <task_id>"
	exit 1
fi

TASK_ID="$1"

aws dynamodb get-item \
	--table-name "${DDB_TASKS_TABLE}" \
	--key "{\"task_id\":{\"S\":\"${TASK_ID}\"}}" \
	--region "${AWS_REGION}"
