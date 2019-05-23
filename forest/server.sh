#!/bin/bash
DATABASE=$1
if [[ "${DATABASE}" == "" ]] ; then
    echo "Please specify DATABASE"
    exit 2
fi
CONFIG_FILE=$2
if [[ "${CONFIG_FILE}" == "" ]] ; then
    echo "Please specify CONFIG_FILE"
    exit 2
fi
bokeh serve app/ --show --args \
    --database ${DATABASE} \
    --config-file ${CONFIG_FILE}
