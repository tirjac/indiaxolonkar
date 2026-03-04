#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# main

if [ -z "${AWS_REGION}" ] || [ -z "${DDB_USERS_TABLE}" ] || [ -z "${DDB_TASKS_TABLE}" ] || [ -z "${TASKS_BY_USER_INDEX}" ] ; then
	echo "Missing AWS_REGION, DDB_USERS_TABLE, DDB_TASKS_TABLE, or TASKS_BY_USER_INDEX"
	exit 1
fi

set -e

echo "Creating DynamoDB tables in ${AWS_REGION}"

if aws dynamodb describe-table --region ${AWS_REGION} --table-name ${DDB_USERS_TABLE} >/dev/null 2>&1 ; then
	echo "Users table exists: ${DDB_USERS_TABLE}"
else
	aws dynamodb create-table \
		--region ${AWS_REGION} \
		--table-name ${DDB_USERS_TABLE} \
		--attribute-definitions AttributeName=user_id,AttributeType=S \
		--key-schema AttributeName=user_id,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST
	echo "Created users table: ${DDB_USERS_TABLE}"
fi

if aws dynamodb describe-table --region ${AWS_REGION} --table-name ${DDB_TASKS_TABLE} >/dev/null 2>&1 ; then
	echo "Tasks table exists: ${DDB_TASKS_TABLE}"
else
	aws dynamodb create-table \
		--region ${AWS_REGION} \
		--table-name ${DDB_TASKS_TABLE} \
		--attribute-definitions \
			AttributeName=task_id,AttributeType=S \
			AttributeName=user_id,AttributeType=S \
			AttributeName=created_at,AttributeType=S \
		--key-schema AttributeName=task_id,KeyType=HASH \
		--global-secondary-indexes \
			"IndexName=${TASKS_BY_USER_INDEX},KeySchema=[{AttributeName=user_id,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL}" \
		--billing-mode PAY_PER_REQUEST
	echo "Created tasks table: ${DDB_TASKS_TABLE}"
fi
