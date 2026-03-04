#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

FUNC=${1:-${CHALICE_APP_NAME}-dev-handle_sqs}
QUEUE_URL=${2:-${SQS_QUEUE_URL}}

if [ -z "${AWS_REGION}" ] ; then echo "AWS_REGION not set" ; exit 1 ; fi
if [ -z "${FUNC}" ] ; then echo "Function name not set" ; exit 1 ; fi
if [ -z "${QUEUE_URL}" ] ; then echo "SQS_QUEUE_URL not set" ; exit 1 ; fi

UUID=$(aws lambda list-event-source-mappings \
	--function-name "${FUNC}" \
	--event-source-arn "${QUEUE_URL}" \
	--region "${AWS_REGION}" \
	--query 'EventSourceMappings[0].UUID' --output text 2>/dev/null)

if [ -z "${UUID}" ] || [ "${UUID}" = "None" ] ; then
	UUID=$(aws lambda list-event-source-mappings \
		--function-name "${FUNC}" \
		--region "${AWS_REGION}" \
		--query 'EventSourceMappings[0].UUID' --output text 2>/dev/null)
fi

if [ -z "${UUID}" ] || [ "${UUID}" = "None" ] ; then
	echo "No event source mapping found for ${FUNC}"
	exit 1
fi

aws lambda update-event-source-mapping \
	--uuid "${UUID}" \
	--enabled true \
	--region "${AWS_REGION}" >/dev/null

echo "Enabled SQS trigger for ${FUNC} (${UUID})"
