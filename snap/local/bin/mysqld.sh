#!/bin/bash

# This script is designed to be a "supervisor process" for MySQL Server.
# Such process is needed for it to be able to restart upon config changes.
# Ref: https://dev.mysql.com/doc/refman/8.0/en/restart.html

export MYSQLD_PARENT_PID=$$
export MYSQLD_RESTART_CODE=16

while true; do
    # For security measures, applications should not be run as sudo.
    # Execute mysqld as the non-sudo user: snap-daemon
    exec "${SNAP}/usr/bin/setpriv" \
        --clear-groups \
        --reuid snap_daemon \
        --regid root \
        -- \
        "${SNAP}/usr/sbin/mysqld" --defaults-file="${SNAP}/etc/my.cnf" &

    wait $!

    EXIT_CODE=$?

    if [ ${EXIT_CODE} -ne ${MYSQLD_RESTART_CODE} ]; then
        echo "MySQL exited with code ${EXIT_CODE}."
        break
    fi
done
