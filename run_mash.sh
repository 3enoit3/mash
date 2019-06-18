#!/bin/bash

# Load configuration
MASH_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${MASH_DIR}/env.sh

# Run
MASH=${MASH_DIR}/mash.py
python ${MASH} -d
