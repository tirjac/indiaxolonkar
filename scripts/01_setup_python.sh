#!/bin/bash

PEXE=${PEXE:="3.12"}
MY_VENV=${MY_VENV:="venv"}

EXTRA=""

if [ "`uname`" = "Darwin" ] ; then
	export DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH}:/opt/homebrew/lib:${MY_VENV}/lib
	export PATH="~/Library/Python/${PEXE}/bin:/usr/local/opt/python@${PEXE}/bin:$PATH"
fi

REQFIL="requirements.txt"

if [ ! -d ${MY_VENV} ] ; then
	python${PEXE} -m venv ${MY_VENV}
	source ${MY_VENV}/bin/activate
	pip install --upgrade pip setuptools wheel build chalice
else
	source ${MY_VENV}/bin/activate
fi

python -m pip install ${EXTRA} -r ${REQFIL}
# python setup.py install
