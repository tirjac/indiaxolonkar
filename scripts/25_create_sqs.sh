#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# main

if [ -z "${AWS_REGION}" ] || [ -z "${SQS_QUEUE_NAME}" ] ; then
	echo "Missing AWS_REGION or SQS_QUEUE_NAME"
	exit 1
fi

set -e

echo "Ensuring SQS queue ${SQS_QUEUE_NAME} in ${AWS_REGION}"

QUEUE_URL=$(aws sqs get-queue-url --queue-name ${SQS_QUEUE_NAME} --region ${AWS_REGION} --output text --query 'QueueUrl' 2>/dev/null || true)
if [ -z "${QUEUE_URL}" ] ; then
	QUEUE_URL=$(aws sqs create-queue \
		--region ${AWS_REGION} \
		--queue-name ${SQS_QUEUE_NAME} \
		--attributes VisibilityTimeout=960 \
		--output text --query 'QueueUrl')
fi

if [ -z "${QUEUE_URL}" ] ; then
	echo "Failed to create or fetch queue URL"
	exit 1
fi

echo "Queue URL: ${QUEUE_URL}"
aws sqs set-queue-attributes \
	--queue-url "${QUEUE_URL}" \
	--attributes VisibilityTimeout=960 \
	--region "${AWS_REGION}"
if [ -n "${MY_PROF}" ] && [ -f "${MY_PROF}" ] ; then
	QUEUE_URL="${QUEUE_URL}" python3 - << 'PY'
import os

path = os.environ.get("MY_PROF", ".env.local")
queue_url = os.environ.get("QUEUE_URL", "")
if not queue_url:
	raise SystemExit(0)

with open(path, "r", encoding="utf-8") as f:
	lines = f.read().splitlines()

out = []
found = False
for line in lines:
	if line.strip() == "None=None" or line.startswith("#SQS_QUEUE_URL="):
		continue
	if line.startswith("SQS_QUEUE_URL="):
		out.append(f"SQS_QUEUE_URL={queue_url}")
		found = True
	else:
		out.append(line)
if not found:
	out.append(f"SQS_QUEUE_URL={queue_url}")

with open(path, "w", encoding="utf-8") as f:
	f.write("\n".join(out) + "\n")
print("OK")
PY
else
	ENV_HINT="${MY_PROF:-.env.local}"
	echo "Set SQS_QUEUE_URL in ${ENV_HINT} to this value."
fi
