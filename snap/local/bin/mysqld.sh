#!/bin/bash

exec "${SNAP}/usr/bin/setpriv" \
    --clear-groups \
    --reuid snap_daemon \
    --regid root \
    -- \
    "${SNAP}/usr/sbin/mysqld" --defaults-file="${SNAP}/etc/my.cnf"
