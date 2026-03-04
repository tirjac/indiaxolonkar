#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ -z "${AWS_REGION}" ] ; then echo "AWS_REGION not set" ; exit 1 ; fi

APP_NAME=${CHALICE_APP_NAME:-$(python3 - << 'PY'
import json
cfg = json.load(open(".chalice/config.json", "r", encoding="utf-8"))
print(cfg.get("app_name", "indiaxolonkar"))
PY
)}
FUNC=${1:-${APP_NAME}-dev}
LIMIT=${2:-50}

LOG_GROUP="/aws/lambda/${FUNC}"

aws logs filter-log-events \
	--log-group-name "${LOG_GROUP}" \
	--max-items "${LIMIT}" \
	--region "${AWS_REGION}" \
	--interleaved
