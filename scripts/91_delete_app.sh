#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# NOTE: This only deletes the Chalice app (API Gateway + Lambdas + IAM role).
# It does NOT delete S3, SQS, or DynamoDB resources.

APP_NAME=${1:-}
STAGE=${2:-dev}
if [ -z "${APP_NAME}" ] ; then
	echo "Usage: $0 <app_name> [stage]"
	exit 1
fi

TMP_CFG=".chalice/config.json"
if [ ! -f "${TMP_CFG}" ] ; then
	echo "Missing .chalice/config.json"
	exit 1
fi

python3 - << PY
import json
cfg_path = ".chalice/config.json"
app_name = "${APP_NAME}"
cfg = json.load(open(cfg_path, "r", encoding="utf-8"))
cfg["app_name"] = app_name
with open(cfg_path, "w", encoding="utf-8") as f:
	json.dump(cfg, f, indent=2, sort_keys=True)
	f.write("\n")
PY

chalice delete --stage "${STAGE}"

echo "OK"
