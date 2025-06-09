#!/bin/bash

exec "${SNAP}/usr/bin/setpriv" \
    --clear-groups \
    --reuid snap_daemon \
    --regid root \
    -- \
    "${@}"
