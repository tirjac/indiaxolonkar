#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ -z "${AWS_REGION}" ] ; then echo "AWS_REGION not set" ; exit 1 ; fi
if [ -z "${SES_FROM_EMAIL}" ] ; then echo "SES_FROM_EMAIL not set" ; exit 1 ; fi

STATUS=$(aws ses get-identity-verification-attributes \
	--identities "${SES_FROM_EMAIL}" \
	--region "${AWS_REGION}" \
	--output json 2>/dev/null | python3 - << 'PY'
import json, sys, os
email = os.environ.get("SES_FROM_EMAIL", "").strip().lower()
raw = sys.stdin.read()
try:
	data = json.loads(raw or "{}")
except Exception:
	print("")
	raise SystemExit
attrs = data.get("VerificationAttributes", {})
status = ""
for k, v in attrs.items():
	if k.lower() == email:
		status = v.get("VerificationStatus", "")
		break
print(status)
PY
)

if [ "${STATUS}" != "Success" ] ; then
	STATUS2=$(aws sesv2 get-email-identity \
		--email-identity "${SES_FROM_EMAIL}" \
		--region "${AWS_REGION}" \
		--query 'VerificationStatus' \
		--output text 2>/dev/null)
	if [ "${STATUS2}" = "SUCCESS" ] ; then
		STATUS="Success"
	fi
fi

if [ -z "${STATUS}" ] || [ "${STATUS}" = "None" ] ; then
	echo "SES_FROM_EMAIL not verified: ${SES_FROM_EMAIL}"
	exit 1
fi

echo "SES_FROM_EMAIL status: ${STATUS}"
