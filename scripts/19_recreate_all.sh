#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))

bash ${SRCDIR}/21_generate_env_local.sh
bash ${SRCDIR}/22_set_required_env.sh
bash ${SRCDIR}/23_create_db.sh
bash ${SRCDIR}/24_create_s3_bucket.sh
bash ${SRCDIR}/25_create_sqs.sh
bash ${SRCDIR}/26_push_env_to_ssm.sh

echo "OK"
echo "RUN bash ${SRCDIR}/17_deploy_dev.sh to deploy"
