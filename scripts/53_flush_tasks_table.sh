#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# main

if [ -z "${DDB_TASKS_TABLE}" ] || [ -z "${AWS_REGION}" ] ; then
	echo "Missing DDB_TASKS_TABLE or AWS_REGION"
	exit 1
fi

set -e

KEYS=$(aws dynamodb scan \
	--table-name "${DDB_TASKS_TABLE}" \
	--attributes-to-get task_id \
	--region "${AWS_REGION}" \
	--query 'Items[].task_id.S' \
	--output text)

if [ -z "${KEYS}" ] ; then
	echo "No items found"
	exit 0
fi

COUNT=0
for k in ${KEYS}; do
	aws dynamodb delete-item \
		--table-name "${DDB_TASKS_TABLE}" \
		--key "{\"task_id\":{\"S\":\"${k}\"}}" \
		--region "${AWS_REGION}" >/dev/null
	COUNT=$((COUNT+1))
done

echo "Deleted ${COUNT} items"
