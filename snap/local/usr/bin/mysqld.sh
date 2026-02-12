#!/bin/bash

exec "${SNAP}/usr/bin/setpriv" \
    --clear-groups \
    --reuid snap_daemon \
    --regid root \
    -- \
    "${SNAP}/usr/bin/mysqld_safe" --defaults-file="${SNAP}/etc/my.cnf"
