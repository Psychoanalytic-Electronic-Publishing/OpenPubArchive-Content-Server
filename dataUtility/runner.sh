#!/bin/sh

if [[ -z "${UTILITY_DIRECTORY}" ]]; then
    echo "UTILITY_DIRECTORY is not set. Exiting."
    exit 1
else if [[ -z "${UTILITY_NAME}" ]]; then
    echo "UTILITY_NAME is not set. Exiting."
    exit 1;
else if [[ -z "${UTILITY_ARGS}" ]]; then
    echo "UTILITY_ARGS is not set. Exiting."
    exit 1;
fi
fi
fi

cd ./$UTILITY_DIRECTORY
python -u $UTILITY_NAME.py $UTILITY_ARGS