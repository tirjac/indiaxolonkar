#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ -z "${AWS_REGION}" ] ; then echo "AWS_REGION not set" ; exit 1 ; fi
if [ -z "${CUSTOM_DOMAIN}" ] ; then echo "CUSTOM_DOMAIN not set" ; exit 1 ; fi
if [ -z "${ACM_CERT_ARN}" ] ; then
	FOUND_ARN=$(aws acm list-certificates --region us-east-1 \
		--query "CertificateSummaryList[?DomainName=='${CUSTOM_DOMAIN}'].CertificateArn | [0]" \
		--output text 2>/dev/null)
	if [ -n "${FOUND_ARN}" ] && [ "${FOUND_ARN}" != "None" ] ; then
		ACM_CERT_ARN="${FOUND_ARN}"
		if [ -n "${MY_PROF}" ] && [ -f "${MY_PROF}" ] ; then
			ACM_CERT_ARN="${ACM_CERT_ARN}" python3 - << 'PY'
import os

path = os.environ.get("MY_PROF", ".env.local")
val = os.environ.get("ACM_CERT_ARN", "")
if not val:
	raise SystemExit(0)

with open(path, "r", encoding="utf-8") as f:
	lines = f.read().splitlines()

out = []
found = False
for line in lines:
	if line.startswith("ACM_CERT_ARN=") or line.startswith("#ACM_CERT_ARN="):
		out.append(f"ACM_CERT_ARN={val}")
		found = True
	else:
		out.append(line)
if not found:
	out.append(f"ACM_CERT_ARN={val}")

with open(path, "w", encoding="utf-8") as f:
	f.write("\n".join(out) + "\n")
PY
		fi
	fi
fi

if [ -z "${ACM_CERT_ARN}" ] ; then
	echo "ACM_CERT_ARN not set. Requesting a certificate in us-east-1 for ${CUSTOM_DOMAIN}."
	CERT_ARN=$(aws acm request-certificate \
		--domain-name "${CUSTOM_DOMAIN}" \
		--validation-method DNS \
		--region us-east-1 \
		--query 'CertificateArn' --output text 2>/dev/null)
	if [ -z "${CERT_ARN}" ] || [ "${CERT_ARN}" = "None" ] ; then
		echo "Unable to request certificate."
		exit 1
	fi
	CERT_ARN="${CERT_ARN}" python3 - << 'PY'
import json
import os
import sys
import subprocess

cert_arn = os.environ.get("CERT_ARN", "")
if not cert_arn:
	sys.exit(0)
try:
	out = subprocess.check_output(
		["aws", "acm", "describe-certificate", "--certificate-arn", cert_arn, "--region", "us-east-1"],
		text=True,
	)
	data = json.loads(out)
except Exception:
	sys.exit(0)

opts = data.get("Certificate", {}).get("DomainValidationOptions", [])
for opt in opts:
	rec = opt.get("ResourceRecord") or {}
	name = rec.get("Name")
	val = rec.get("Value")
	if name and val:
		print("Add this CNAME record:")
		print(f"Name: {name}")
		print(f"Value: {val}")
PY
	echo "Set the DNS CNAME above, wait for validation, then re-run this script with ACM_CERT_ARN set."
	exit 0
fi

CFG_APP_NAME=$(python3 - << 'PY'
import json
cfg = json.load(open(".chalice/config.json", "r", encoding="utf-8"))
print(cfg.get("app_name", "indiaxolonkar"))
PY
)
STAGE=$(python3 - << 'PY'
import json
cfg = json.load(open(".chalice/config.json", "r", encoding="utf-8"))
stage = cfg.get("stages", {}).get("dev", {}).get("api_gateway_stage", "api")
print(stage)
PY
)

API_ID=""
APP_NAME=""

CHALICE_URL=$(chalice url --stage dev 2>/dev/null || true)
API_ID_FROM_URL=$(echo "${CHALICE_URL}" | sed -n 's#https://\([^.]*\)\.execute-api\.\([^.]*\)\.amazonaws\.com.*#\1#p')
API_REGION_FROM_URL=$(echo "${CHALICE_URL}" | sed -n 's#https://\([^.]*\)\.execute-api\.\([^.]*\)\.amazonaws\.com.*#\2#p')

if [ -n "${API_REGION_FROM_URL}" ] && [ "${API_REGION_FROM_URL}" != "${AWS_REGION}" ] ; then
	echo "Using AWS_REGION from chalice url: ${API_REGION_FROM_URL}"
	AWS_REGION="${API_REGION_FROM_URL}"
fi

if [ -n "${API_ID_FROM_URL}" ] ; then
	API_ID="${API_ID_FROM_URL}"
	APP_NAME="${CHALICE_APP_NAME:-${CFG_APP_NAME}}"
else
	echo "Unable to parse API id from chalice url."
	echo "Run: chalice url --stage dev and ensure it returns an execute-api URL."
	exit 1
fi

echo "Using API_ID=${API_ID}"

if aws apigateway get-domain-name --domain-name "${CUSTOM_DOMAIN}" --region "${AWS_REGION}" >/dev/null 2>&1 ; then
	echo "Custom domain exists: ${CUSTOM_DOMAIN}"
else
	echo "Creating custom domain ${CUSTOM_DOMAIN}"
	aws apigateway create-domain-name \
		--domain-name "${CUSTOM_DOMAIN}" \
		--certificate-arn "${ACM_CERT_ARN}" \
		--endpoint-configuration types=EDGE \
		--region "${AWS_REGION}" >/dev/null
fi

echo "Updating base path mapping to API ${API_ID} stage ${STAGE}"
aws apigateway delete-base-path-mapping \
	--domain-name "${CUSTOM_DOMAIN}" \
	--base-path "(none)" \
	--region "${AWS_REGION}" >/dev/null 2>&1 || true

aws apigateway create-base-path-mapping \
	--domain-name "${CUSTOM_DOMAIN}" \
	--rest-api-id "${API_ID}" \
	--stage "${STAGE}" \
	--region "${AWS_REGION}" >/dev/null

TARGET=$(aws apigateway get-domain-name --domain-name "${CUSTOM_DOMAIN}" --region "${AWS_REGION}" \
	--query 'distributionDomainName' --output text)
if [ -n "${TARGET}" ] && [ "${TARGET}" != "None" ] ; then
	echo "CNAME ${CUSTOM_DOMAIN} -> ${TARGET}"
	echo "Reminder: create this CNAME in DNS if not already set."
fi

echo "OK"
