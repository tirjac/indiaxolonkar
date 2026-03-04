#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ -z "${MY_PROF}" ] ; then echo "MY_PROF not set" ; exit 1 ; fi
if [ ! -f "${MY_PROF}" ] ; then echo "Missing ${MY_PROF}" ; exit 1 ; fi

REQ_VARS=(
	AWS_REGION
	SSM_PARAM_NAME
	CHALICE_APP_NAME
	S3_BUCKET
	SQS_QUEUE_NAME
	SQS_QUEUE_URL
	DDB_TASKS_TABLE
	DDB_USERS_TABLE
	TASKS_BY_USER_INDEX
	SES_FROM_EMAIL
	OPENAI_API_KEY
)

echo "Checking required env vars from ${MY_PROF}"
MISSING=0
for V in "${REQ_VARS[@]}"; do
	if [ -z "${!V}" ] ; then
		echo "Missing: ${V}"
		MISSING=1
	fi
done
if [ "${MISSING}" -ne 0 ] ; then
	echo "Set missing vars in ${MY_PROF}"
	echo "Cannot Deploy"
	exit 1
fi

FAIL=0

echo "Checking SES_FROM_EMAIL verification"
SES_STATUS=$(aws ses get-identity-verification-attributes \
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
if [ "${SES_STATUS}" != "Success" ] ; then
	SES_STATUS2=$(aws sesv2 get-email-identity \
		--email-identity "${SES_FROM_EMAIL}" \
		--region "${AWS_REGION}" \
		--query 'VerificationStatus' \
		--output text 2>/dev/null)
	if [ "${SES_STATUS2}" = "SUCCESS" ] ; then
		SES_STATUS="Success"
	fi
fi
if [ -z "${SES_STATUS}" ] || [ "${SES_STATUS}" = "None" ] || [ "${SES_STATUS}" = "Pending" ] ; then
	echo "SES_FROM_EMAIL not verified: ${SES_FROM_EMAIL}"
	echo "Run: sh scripts/31_verify_send_ses_from_mail.sh"
	FAIL=1
fi

echo "Checking AWS resources"
aws s3api head-bucket --bucket "${S3_BUCKET}" --region "${AWS_REGION}" >/dev/null 2>&1 || { echo "Missing S3 bucket: ${S3_BUCKET}"; FAIL=1; }
aws sqs get-queue-url --queue-name "${SQS_QUEUE_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1 || { echo "Missing SQS queue in region ${AWS_REGION}: ${SQS_QUEUE_NAME}"; FAIL=1; }
aws sqs get-queue-attributes --queue-url "${SQS_QUEUE_URL}" --attribute-names ApproximateNumberOfMessages --region "${AWS_REGION}" >/dev/null 2>&1 || { echo "Missing SQS queue URL: ${SQS_QUEUE_URL}"; FAIL=1; }
aws dynamodb describe-table --table-name "${DDB_TASKS_TABLE}" --region "${AWS_REGION}" >/dev/null 2>&1 || { echo "Missing DDB table: ${DDB_TASKS_TABLE}"; FAIL=1; }
aws dynamodb describe-table --table-name "${DDB_USERS_TABLE}" --region "${AWS_REGION}" >/dev/null 2>&1 || { echo "Missing DDB table: ${DDB_USERS_TABLE}"; FAIL=1; }

echo "Checking SQS visibility timeout vs Lambda timeout"
python3 - << 'PY'
import json
import os
import subprocess
import sys

queue_url = os.environ.get("SQS_QUEUE_URL", "")
region = os.environ.get("AWS_REGION", "")

cfg = json.load(open(".chalice/config.json", "r", encoding="utf-8"))
stages = cfg.get("stages", {})
lambda_timeout = None
for stage in stages.values():
	if "lambda_timeout" in stage:
		lambda_timeout = stage["lambda_timeout"]
		break
if lambda_timeout is None:
	lambda_timeout = 60

try:
	out = subprocess.check_output(
		[
			"aws",
			"sqs",
			"get-queue-attributes",
			"--queue-url",
			queue_url,
			"--attribute-names",
			"VisibilityTimeout",
			"--region",
			region,
		],
		text=True,
	)
	data = json.loads(out)
	vis = int(data.get("Attributes", {}).get("VisibilityTimeout", "0"))
	if vis < int(lambda_timeout):
		print(f"Visibility timeout {vis}s is less than lambda_timeout {lambda_timeout}s")
		sys.exit(2)
	else:
		print(f"Visibility timeout OK: {vis}s >= lambda_timeout {lambda_timeout}s")
except Exception:
	print("Unable to check SQS visibility timeout.")
	sys.exit(2)
PY
if [ $? -ne 0 ] ; then FAIL=1 ; fi

echo "Checking IAM policy attachment for SSM"
BASE_NAME=${APP_DEFAULT_PREFIX:-indiaxolonkar}
APP_NAME=${CHALICE_APP_NAME:-$(python3 - << 'PY'
import json
cfg = json.load(open(".chalice/config.json", "r", encoding="utf-8"))
print(cfg.get("app_name", "indiaxolonkar"))
PY
)}
ROLE_NAME=${APP_NAME}-dev
POLICY_NAME=${BASE_NAME}-app-policy
NEED_POLICY=0
aws iam list-role-policies --role-name "${ROLE_NAME}" --query 'PolicyNames' --output text 2>/dev/null | grep -q "${POLICY_NAME}" || { echo "Missing IAM inline policy: ${POLICY_NAME} on role ${ROLE_NAME}"; NEED_POLICY=1; }

echo "Checking SSM parameter matches ${MY_PROF}"
python3 - << 'PY'
import json
import os
import subprocess
import sys

env_path = os.environ.get("MY_PROF", ".env.local")
param_name = os.environ.get("SSM_PARAM_NAME", "")
region = os.environ.get("AWS_REGION", "")
optional_keys = {"CUSTOM_DOMAIN", "ACM_CERT_ARN"}

def parse_env(path):
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
            if not key or val == "":
                continue
            env[key] = val
    return env

if not param_name or not region:
    print("SSM_PARAM_NAME or AWS_REGION missing.")
    sys.exit(2)

try:
    out = subprocess.check_output(
        [
            "aws",
            "ssm",
            "get-parameter",
            "--name",
            param_name,
            "--with-decryption",
            "--region",
            region,
        ],
        text=True,
    )
except Exception:
    print("Unable to fetch SSM parameter for comparison.")
    sys.exit(2)

payload = json.loads(out)
val = payload.get("Parameter", {}).get("Value") or "{}"
try:
    ssm = json.loads(val)
except json.JSONDecodeError:
    print("SSM parameter value is not valid JSON.")
    sys.exit(2)

env = parse_env(env_path)
missing = []
mismatch = []
for k, v in env.items():
    if k in optional_keys:
        continue
    if k not in ssm:
        missing.append(k)
    elif str(ssm.get(k)) != v:
        mismatch.append(k)

if missing:
    print("SSM missing keys:", ", ".join(sorted(missing)))
if mismatch:
    print("SSM value mismatch keys:", ", ".join(sorted(mismatch)))
if not missing and not mismatch:
    print(f"SSM matches {env_path}")
if missing or mismatch:
    sys.exit(2)
PY
if [ $? -ne 0 ] ; then FAIL=1 ; fi

if [ -n "${CUSTOM_DOMAIN}" ] ; then
	echo "Checking CUSTOM_DOMAIN CNAME"
	python3 - << 'PY'
import os
import sys
import json
import subprocess

domain = os.environ.get("CUSTOM_DOMAIN", "").strip()
if not domain:
	sys.exit(0)

region = os.environ.get("AWS_REGION", "").strip()
if not region:
	print("AWS_REGION not set; cannot verify CUSTOM_DOMAIN.")
	sys.exit(1)

try:
	out = subprocess.check_output(
		["aws", "apigateway", "get-domain-name", "--domain-name", domain, "--region", region],
		text=True,
	)
	payload = json.loads(out)
	dist = payload.get("distributionDomainName") or payload.get("regionalDomainName")
	if dist:
		print("CUSTOM_DOMAIN exists in API Gateway.")
		sys.exit(0)
except Exception:
	pass

print("CUSTOM_DOMAIN not found in API Gateway yet.")
print("Ignoring CUSTOM_DOMAIN as no mapping exists yet.")
sys.exit(1)
PY
	if [ $? -ne 0 ] ; then
		echo "CUSTOM_DOMAIN will be ignored for deploy."
		echo "1" > .chalice/skip_custom_domain 2>/dev/null || true
	else
		echo "0" > .chalice/skip_custom_domain 2>/dev/null || true
	fi
fi

echo "Compile check"
python3 -m py_compile chalicelib/worker.py chalicelib/handlers.py chalicelib/tasks.py chalicelib/auth.py app.py || FAIL=1

echo "${NEED_POLICY}" > .chalice/need_policy 2>/dev/null || true

if [ "${FAIL}" -ne 0 ] ; then
	echo "Predeploy check failed."
	echo "Cannot Deploy"
	exit 1
fi

echo "Predeploy check complete."
