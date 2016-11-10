#!/bin/bash

pAA_scrip_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

ACTIVATE="${pAA_scrip_DIR}/../venv/bin/activate"

echo $ACTIVATE

if [ -f $ACTIVATE ]; then
    echo activate venv
    source $ACTIVATE
else
    echo venv does NOT exist
fi

${pAA_scrip_DIR}/pAA_diarization.py $@


