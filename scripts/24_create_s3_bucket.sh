#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# main

if [ -z "${AWS_REGION}" ] || [ -z "${S3_BUCKET}" ] ; then
	echo "Missing AWS_REGION or S3_BUCKET"
	exit 1
fi

set -e

echo "Creating S3 bucket ${S3_BUCKET} in ${AWS_REGION}"

if aws s3api head-bucket --bucket ${S3_BUCKET} >/dev/null 2>&1 ; then
	echo "Bucket exists: ${S3_BUCKET}"
else
if [ "${AWS_REGION}" = "us-east-1" ] ; then
	aws s3api create-bucket --bucket ${S3_BUCKET} --region ${AWS_REGION}
else
	aws s3api create-bucket --bucket ${S3_BUCKET} --region ${AWS_REGION} \
		--create-bucket-configuration LocationConstraint=${AWS_REGION}
fi
	echo "Created bucket: ${S3_BUCKET}"
fi

# Allow public read for objects (required for public image URLs)
aws s3api put-public-access-block --bucket ${S3_BUCKET} \
	--public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

cat <<POLICY > /tmp/${S3_BUCKET}_policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
    }
  ]
}
POLICY

aws s3api put-bucket-policy --bucket ${S3_BUCKET} --policy file:///tmp/${S3_BUCKET}_policy.json

echo "Bucket policy applied for public read."
