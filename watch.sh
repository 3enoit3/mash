#!/bin/bash

# dependencies: sudo apt-get install entr pylint

SCRIPT=mash.py
MODULE=${SCRIPT%%\.py}

# Load configuration
MASH_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${MASH_DIR}/env.sh

# Watch
echo ${SCRIPT} | entr -c sh -c "pylint --reports=n ${SCRIPT} && python -m unittest ${MODULE}"
