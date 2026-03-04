#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# main

if [ -z "${SQS_QUEUE_URL}" ] ; then
	echo "SQS_QUEUE_URL not set"
	exit 1
fi

MAX=${1:-1}
WAIT=${2:-5}

aws sqs receive-message \
	--queue-url "${SQS_QUEUE_URL}" \
	--max-number-of-messages ${MAX} \
	--wait-time-seconds ${WAIT} \
	--region "${AWS_REGION}"
