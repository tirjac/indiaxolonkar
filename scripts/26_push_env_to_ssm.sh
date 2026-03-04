#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ -z "${AWS_REGION}" ] ; then echo "AWS_REGION not set" ; exit 1 ; fi
if [ -z "${SSM_PARAM_NAME}" ] ; then echo "SSM_PARAM_NAME not set" ; exit 1 ; fi
if [ -z "${MY_PROF}" ] ; then echo "MY_PROF not set" ; exit 1 ; fi
if [ ! -f "${MY_PROF}" ] ; then echo "Missing ${MY_PROF}" ; exit 1 ; fi

JSON_VAL=$(python3 - << 'PY'
import json
import os

path = os.environ.get("MY_PROF", ".env.local")
env = {}
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key or key == "None" or val == "":
            continue
        env[key] = val

print(json.dumps(env))
PY
)

if [ -z "${JSON_VAL}" ] ; then echo "No values found in ${MY_PROF}" ; exit 1 ; fi

aws ssm put-parameter \
	--name "${SSM_PARAM_NAME}" \
	--type "SecureString" \
	--value "${JSON_VAL}" \
	--overwrite \
	--region "${AWS_REGION}"

echo "OK"
