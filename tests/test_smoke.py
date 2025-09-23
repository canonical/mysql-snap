# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import subprocess
import time

import yaml


def test_all_apps():
    with open("snap/snapcraft.yaml") as file:
        snapcraft = yaml.safe_load(file)

    override = {}
    skip = []

    snap_apps = snapcraft["apps"]
    snap_name = snapcraft["name"]

    for app, data in snap_apps.items():
        if bool(data.get("daemon")) or app in skip:
            continue

        if app == snap_name:
            command = f"{snap_name}"
        else:
            command = f"{snap_name}.{app}"

        print(f"Running {command}...")
        subprocess.check_output(
            f"sudo {command} {override.get(app, '--version')}".split()
        )


def test_all_services():
    with open("snap/snapcraft.yaml") as file:
        snapcraft = yaml.safe_load(file)

    skip = []

    snap_apps = snapcraft["apps"]
    snap_name = snapcraft["name"]

    for app, data in snap_apps.items():
        if not bool(data.get("daemon")) or app in skip:
            continue

        print(f"Running {snap_name}.{app}...")
        subprocess.check_output(f"sudo snap start {snap_name}.{app}".split())

        time.sleep(5)
        service = subprocess.check_output(f"snap services {snap_name}.{app}".split())
        subprocess.check_output(f"sudo snap stop {snap_name}.{app}".split())

        assert "active" in service.decode()
