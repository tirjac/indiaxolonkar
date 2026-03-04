#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ -z "${AWS_REGION}" ] ; then echo "AWS_REGION not set" ; exit 1 ; fi

BASE_NAME=${APP_DEFAULT_PREFIX:-indiaxolonkar}
STAGE=${1:-dev}

echo "Teardown for ${BASE_NAME} (${STAGE}) in ${AWS_REGION}"

echo "0) Delete API Gateway base path mappings (if CUSTOM_DOMAIN set)"
if [ -n "${CUSTOM_DOMAIN}" ] ; then
	python3 - << 'PY'
import json
import os
import subprocess

domain = os.environ.get("CUSTOM_DOMAIN", "").strip()
region = os.environ.get("AWS_REGION", "").strip()
if not domain or not region:
	raise SystemExit(0)

try:
	out = subprocess.check_output(
		[
			"aws",
			"apigateway",
			"get-base-path-mappings",
			"--domain-name",
			domain,
			"--region",
			region,
		],
		text=True,
	)
	payload = json.loads(out)
except Exception:
	raise SystemExit(0)

for item in payload.get("items", []):
	base_path = item.get("basePath") or "(none)"
	subprocess.call(
		[
			"aws",
			"apigateway",
			"delete-base-path-mapping",
			"--domain-name",
			domain,
			"--base-path",
			base_path,
			"--region",
			region,
		]
	)
PY
fi

echo "1) Chalice delete"
chalice delete --stage "${STAGE}" || true

echo "2) Delete Lambda log groups"
aws logs delete-log-group --log-group-name "/aws/lambda/${BASE_NAME}-${STAGE}" --region "${AWS_REGION}" || true
aws logs delete-log-group --log-group-name "/aws/lambda/${BASE_NAME}-${STAGE}-handle_sqs" --region "${AWS_REGION}" || true

echo "3) Delete SQS queue"
if [ -n "${SQS_QUEUE_URL}" ] ; then
	aws sqs delete-queue --queue-url "${SQS_QUEUE_URL}" --region "${AWS_REGION}" || true
fi

echo "4) Delete DynamoDB tables"
if [ -n "${DDB_TASKS_TABLE}" ] ; then
	aws dynamodb delete-table --table-name "${DDB_TASKS_TABLE}" --region "${AWS_REGION}" || true
	aws dynamodb wait table-not-exists --table-name "${DDB_TASKS_TABLE}" --region "${AWS_REGION}" || true
fi
if [ -n "${DDB_USERS_TABLE}" ] ; then
	aws dynamodb delete-table --table-name "${DDB_USERS_TABLE}" --region "${AWS_REGION}" || true
	aws dynamodb wait table-not-exists --table-name "${DDB_USERS_TABLE}" --region "${AWS_REGION}" || true
fi

echo "5) Delete SSM parameter"
if [ -n "${SSM_PARAM_NAME}" ] ; then
	aws ssm delete-parameter --name "${SSM_PARAM_NAME}" --region "${AWS_REGION}" || true
fi

echo "6) Delete S3 bucket"
if [ -n "${S3_BUCKET}" ] ; then
	python3 - << 'PY'
import os
import boto3

bucket = os.environ.get("S3_BUCKET")
region = os.environ.get("AWS_REGION")
if not bucket:
	raise SystemExit(0)

s3 = boto3.client("s3", region_name=region)

# Abort multipart uploads
try:
	p = s3.get_paginator("list_multipart_uploads")
	for page in p.paginate(Bucket=bucket):
		for up in page.get("Uploads", []):
			s3.abort_multipart_upload(
				Bucket=bucket,
				Key=up["Key"],
				UploadId=up["UploadId"],
			)
except Exception:
	pass

# Delete all versions and delete markers (handles versioned buckets)
to_delete = []
def flush():
	if to_delete:
		s3.delete_objects(Bucket=bucket, Delete={"Objects": to_delete, "Quiet": True})
		to_delete.clear()

try:
	p = s3.get_paginator("list_object_versions")
	for page in p.paginate(Bucket=bucket):
		for v in page.get("Versions", []):
			to_delete.append({"Key": v["Key"], "VersionId": v["VersionId"]})
			if len(to_delete) >= 1000:
				flush()
		for m in page.get("DeleteMarkers", []):
			to_delete.append({"Key": m["Key"], "VersionId": m["VersionId"]})
			if len(to_delete) >= 1000:
				flush()
	flush()
except Exception:
	pass
PY
	aws s3 rm "s3://${S3_BUCKET}" --recursive --region "${AWS_REGION}" || true
	aws s3api delete-bucket --bucket "${S3_BUCKET}" --region "${AWS_REGION}" || true
fi

echo "7) Delete IAM inline policy (if present)"
aws iam delete-role-policy --role-name "${BASE_NAME}-${STAGE}" --policy-name "${BASE_NAME}-app-policy" || true

echo "Teardown complete."
