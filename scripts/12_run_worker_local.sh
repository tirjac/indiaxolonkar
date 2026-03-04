#!/bin/bash
export SRCDIR=$(dirname $(cd ${0%/*} 2>>/dev/null ; echo `pwd`/${0##*/}))
. ${SRCDIR}/00_script_config.sh

# main

# Usage: $0 [max_messages] [wait_seconds] [--loop] [--verbose]
if [ $# -eq 0 ] ; then
	MAX=5
	WAIT=10
	EXTRA="--loop"
else
	MAX=${1:-1}
	WAIT=${2:-10}
	shift 2 || true
	EXTRA="$@"
fi

python -m src.run_worker_poll_sqs --max ${MAX} --wait ${WAIT} ${EXTRA}
