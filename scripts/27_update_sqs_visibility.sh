#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ -z "${AWS_REGION}" ] || [ -z "${SQS_QUEUE_URL}" ] ; then
	echo "Missing AWS_REGION or SQS_QUEUE_URL"
	exit 1
fi

VIS=${1:-960}
echo "Updating SQS visibility timeout to ${VIS}s for ${SQS_QUEUE_URL}"

aws sqs set-queue-attributes \
	--queue-url "${SQS_QUEUE_URL}" \
	--attributes VisibilityTimeout="${VIS}" \
	--region "${AWS_REGION}"
