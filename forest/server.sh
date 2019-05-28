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
PORT=8080
bokeh serve app/ \
    --dev \
    --port ${PORT} \
    --allow-websocket-origin eld388:${PORT} \
    --allow-websocket-origin localhost:${PORT} \
    --args \
    --database ${DATABASE} \
    --config-file ${CONFIG_FILE}
