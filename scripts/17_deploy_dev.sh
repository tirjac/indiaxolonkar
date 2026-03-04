#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

python3 - << 'PY'
import json
import os

cfg_path = ".chalice/config.json"
ssm = os.environ.get("SSM_PARAM_NAME", "").strip()
app_name = os.environ.get("CHALICE_APP_NAME", "").strip()
custom_domain = os.environ.get("CUSTOM_DOMAIN", "").strip()
if not ssm:
	raise SystemExit("SSM_PARAM_NAME missing")
if not app_name:
	raise SystemExit("CHALICE_APP_NAME missing")

with open(cfg_path, "r", encoding="utf-8") as f:
	cfg = json.load(f)

cfg["app_name"] = app_name
stages = cfg.get("stages", {})
dev = stages.get("dev", {})
env_vars = dev.get("environment_variables", {})
env_vars["SSM_PARAM_NAME"] = ssm
skip_path = ".chalice/skip_custom_domain"
skip_custom = False
try:
	with open(skip_path, "r", encoding="utf-8") as f:
		skip_custom = f.read().strip() == "1"
except FileNotFoundError:
	skip_custom = False
if custom_domain and not skip_custom:
	env_vars["CUSTOM_DOMAIN"] = custom_domain
elif "CUSTOM_DOMAIN" in env_vars:
	env_vars.pop("CUSTOM_DOMAIN", None)
dev["environment_variables"] = env_vars
stages["dev"] = dev
cfg["stages"] = stages

with open(cfg_path, "w", encoding="utf-8") as f:
	json.dump(cfg, f, indent=2, sort_keys=True)
	f.write("\n")
print("OK")
PY

sh ${SRCDIR}/16_predeploy_check.sh || exit 1
rm -f .chalice/deployments/*.zip .chalice/deployments/*.json 2>/dev/null || true
chalice deploy --stage dev

if [ -f .chalice/need_policy ] ; then
	NEED_POLICY=$(cat .chalice/need_policy)
	if [ "${NEED_POLICY}" = "1" ] ; then
		sh ${SRCDIR}/28_attach_policy.sh
	fi
fi

# Post-deploy: re-check policy attachment (role may not exist before deploy).
BASE_NAME=${APP_DEFAULT_PREFIX:-indiaxolonkar}
ROLE_NAME=${CHALICE_APP_NAME}-dev
POLICY_NAME=${BASE_NAME}-app-policy
aws iam list-role-policies --role-name "${ROLE_NAME}" --query 'PolicyNames' --output text 2>/dev/null | grep -q "${POLICY_NAME}" || {
	echo "Attaching missing IAM policy ${POLICY_NAME} to role ${ROLE_NAME}"
	sh ${SRCDIR}/28_attach_policy.sh "${ROLE_NAME}" "${POLICY_NAME}"
}
