#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
export MY_PROF=${MY_PROF:=".env.local"}

if [ -z "${MY_PROF}" ] ; then echo "MY_PROF not set" ; exit 1 ; fi
if [ -f "${MY_PROF}" ] ; then echo "${MY_PROF} already set" ; exit 1 ; fi

PROJ="indiaxolonkar"
DATEV=`date +'%Y%m%d-%H%M%S'`
PROJNAME="${PROJ}-${DATEV}"
APP_NAME="${PROJNAME}"

cat << EOFF > "${MY_PROF}"
AWS_REGION=us-east-1
APP_DEFAULT_PREFIX=${PROJNAME}
#SQS_QUEUE_URL=
S3_BUCKET=${PROJNAME}-bucket
SQS_QUEUE_NAME=${PROJNAME}-image-jobs
DDB_USERS_TABLE=${PROJNAME}-users
DDB_TASKS_TABLE=${PROJNAME}-tasks
SSM_PARAM_NAME=${PROJNAME}-config
TASKS_BY_USER_INDEX=${PROJNAME}-user_id-created_at-index
#SES_FROM_EMAIL=${SES_FROM_EMAIL}
#OPENAI_API_KEY=${OPENAI_API_KEY}
REQUIRE_EMAIL_VERIFICATION=true
DEBUG_MODE=false
CHALICE_APP_NAME=${APP_NAME}
#CUSTOM_DOMAIN=${CUSTOM_DOMAIN}
EOFF

echo "NOTE: Please set the following vars in ${MY_PROF}:"
grep "^#" "${MY_PROF}"



if [ ! -f ".chalice/config.json" ] ; then
	mkdir -p .chalice
	cat << EOFF > .chalice/config.json
{
  "version": "2.0",
  "app_name": "${PROJNAME}",
  "stages": {
    "dev": {
      "api_gateway_stage": "api",
      "lambda_timeout": 900,
      "lambda_memory_size": 512
    }
  },
  "binary_types": [
    "multipart/form-data",
    "application/octet-stream",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
    "image/bmp",
    "image/tiff"
  ]
}
EOFF
	echo "Created .chalice/config.json"
fi
