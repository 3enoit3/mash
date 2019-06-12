#!/bin/bash

# Load configuration
MASH_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${MASH_DIR}/env.sh

# Setup dirs
mkdir -p ${MASH_RUNTIME_DIR}
mkdir -p ${MASH_BIN_DIR}
mkdir -p ${MASH_DATA_DIR}

# Upgrade youtube-dl
YDL=${MASH_BIN_DIR}/youtube-dl
if [ -f "${YDL}" ]; then
    ${YDL} -U
else
    wget https://yt-dl.org/downloads/latest/youtube-dl -O ${YDL}
    chmod a+rx ${YDL}
fi

# Upgrade mash
git -C ${MASH_DIR} pull --rebase

# Upgrade services
cp ${MASH_DIR}/services/* /etc/systemd/system
systemctl enable mash_upgrade.service
systemctl enable mash_http.service
systemctl enable mash.timer
systemctl enable mash.service
