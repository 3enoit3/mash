#!/bin/bash

SCRIPT=mash.py
MODULE=${SCRIPT%%\.py}

echo ${SCRIPT} | entr sh -c "clear; pylint --reports=n ${SCRIPT} && python -m unittest ${MODULE}"
