#!/bin/bash
export MY_VENV=${MY_VENV:="venv"}
export MY_PROF=${MY_PROF:=".env.local"}

if [ "`uname`" = "Darwin" ] ; then
	export DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH}:/opt/homebrew/lib:${MY_VENV}/lib
fi

if [ ! -d ${MY_VENV} ] ; then echo "DIR  ${MY_VENV} missing"; exit 1; fi
if [ ! -f ${MY_PROF} ] ; then echo "FILE ${MY_PROF} missing , run scripts/21_generate_env_local.sh"; exit 1; fi

 . ${MY_VENV}/bin/activate
set -a
 . ${MY_PROF}
set +a

if [ -n "${AWS_REGION}" ] && [ -z "${AWS_DEFAULT_REGION}" ] ; then
	export AWS_DEFAULT_REGION="${AWS_REGION}"
fi

export PYTHONPATH="."
