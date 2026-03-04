#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

BASE_NAME=${APP_DEFAULT_PREFIX:-indiaxolonkar}
APP_NAME=${CHALICE_APP_NAME:-$(python3 - << 'PY'
import json
cfg = json.load(open(".chalice/config.json", "r", encoding="utf-8"))
print(cfg.get("app_name", "indiaxolonkar"))
PY
)}
ROLE_NAME=${1:-${APP_NAME}-dev}
POLICY_NAME=${2:-${BASE_NAME}-app-policy}

if [ -z "${AWS_REGION}" ] ; then echo "AWS_REGION not set" ; exit 1 ; fi
if [ -z "${SSM_PARAM_NAME}" ] ; then echo "SSM_PARAM_NAME not set" ; exit 1 ; fi
if [ -z "${S3_BUCKET}" ] ; then echo "S3_BUCKET not set" ; exit 1 ; fi
if [ -z "${SQS_QUEUE_URL}" ] ; then echo "SQS_QUEUE_URL not set" ; exit 1 ; fi
if [ -z "${DDB_USERS_TABLE}" ] ; then echo "DDB_USERS_TABLE not set" ; exit 1 ; fi
if [ -z "${DDB_TASKS_TABLE}" ] ; then echo "DDB_TASKS_TABLE not set" ; exit 1 ; fi
if [ -z "${TASKS_BY_USER_INDEX}" ] ; then echo "TASKS_BY_USER_INDEX not set" ; exit 1 ; fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "${ACCOUNT_ID}" ] || [ "${ACCOUNT_ID}" = "None" ] ; then
	echo "Unable to determine AWS account id"
	exit 1
fi

SQS_ARN=$(aws sqs get-queue-attributes --queue-url "${SQS_QUEUE_URL}" --attribute-names QueueArn --region "${AWS_REGION}" --query 'Attributes.QueueArn' --output text 2>/dev/null)
if [ -z "${SQS_ARN}" ] || [ "${SQS_ARN}" = "None" ] ; then
	SQS_ARN="*"
fi

TMPFILE=$(mktemp)
cat << EOF > "${TMPFILE}"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:${AWS_REGION}:${ACCOUNT_ID}:parameter/${SSM_PARAM_NAME}"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:DescribeTable"
      ],
      "Resource": [
        "arn:aws:dynamodb:${AWS_REGION}:${ACCOUNT_ID}:table/${DDB_USERS_TABLE}",
        "arn:aws:dynamodb:${AWS_REGION}:${ACCOUNT_ID}:table/${DDB_TASKS_TABLE}",
        "arn:aws:dynamodb:${AWS_REGION}:${ACCOUNT_ID}:table/${DDB_TASKS_TABLE}/index/${TASKS_BY_USER_INDEX}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "${SQS_ARN}"
    },
    {
      "Effect": "Allow",
      "Action": "ses:SendEmail",
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
	--role-name "${ROLE_NAME}" \
	--policy-name "${POLICY_NAME}" \
	--policy-document "file://${TMPFILE}"

rm -f "${TMPFILE}"

echo "OK"
