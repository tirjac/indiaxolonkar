#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

if [ -z "${MY_PROF}" ] ; then echo "MY_PROF not set" ; exit 1 ; fi
if [ ! -f "${MY_PROF}" ] ; then echo "Missing ${MY_PROF}" ; exit 1 ; fi

set_value () {
	KEY="$1"
	VAL="$2"
	SRC="$3"
	if [ -z "${VAL}" ] ; then
		return
	fi
	KEY="${KEY}" VAL="${VAL}" python3 - << PY
import os

path = os.environ.get("MY_PROF", ".env.local")
key = os.environ.get("KEY")
val = os.environ.get("VAL")

with open(path, "r", encoding="utf-8") as f:
	lines = f.read().splitlines()

out = []
found = False
for line in lines:
	if line.startswith(f"{key}=") or line.startswith(f"#{key}="):
		out.append(f"{key}={val}")
		found = True
	else:
		out.append(line)
if not found:
	out.append(f"{key}={val}")

with open(path, "w", encoding="utf-8") as f:
	f.write("\n".join(out) + "\n")
PY
	echo "${KEY} added from ${SRC}"
}

if [ -n "${SES_FROM_EMAIL}" ] ; then
	set_value "SES_FROM_EMAIL" "${SES_FROM_EMAIL}" "env"
else
	read -p "Enter SES_FROM_EMAIL: " SES_INPUT
	set_value "SES_FROM_EMAIL" "${SES_INPUT}" "input"
fi

if [ -n "${OPENAI_API_KEY}" ] ; then
	set_value "OPENAI_API_KEY" "${OPENAI_API_KEY}" "env"
else
	read -p "Enter OPENAI_API_KEY: " OPENAI_INPUT
	set_value "OPENAI_API_KEY" "${OPENAI_INPUT}" "input"
fi

if [ -n "${CUSTOM_DOMAIN}" ] ; then
	set_value "CUSTOM_DOMAIN" "${CUSTOM_DOMAIN}" "env"
else
	read -p "Enter CUSTOM_DOMAIN (optional): " CUSTOM_INPUT
	if [ -n "${CUSTOM_INPUT}" ] ; then
		set_value "CUSTOM_DOMAIN" "${CUSTOM_INPUT}" "input"
	fi
fi

echo "OK"
