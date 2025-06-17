# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import subprocess
import time

import pytest
import yaml


def test_install():
    with open("snap/snapcraft.yaml") as file:
        snapcraft = yaml.safe_load(file)

    snap_name = snapcraft['name']
    snap_version = snapcraft['version']

    subprocess.run(
        f"sudo snap remove --purge {snap_name}".split(),
        check=True,
    )
    subprocess.run(
        f"sudo snap install ./{snap_name}_{snap_version}_amd64.snap --devmode".split(),
        check=True,
    )


@pytest.mark.run(after="test_install")
def test_all_apps():
    with open("snap/snapcraft.yaml") as file:
        snapcraft = yaml.safe_load(file)

    override = {"mysqladmin": "--print-defaults"}
    skip = []

    snap_apps = snapcraft["apps"]
    snap_name = snapcraft['name']

    for app, data in snap_apps.items():
        if bool(data.get("daemon")) or app in skip:
            continue

        if app == snap_name:
            command = f"{snap_name}"
        else:
            command = f"{snap_name}.{app}"

        print(f"Running {command}...")
        subprocess.check_output(
            f"sudo {command} {override.get(app, '--help')}".split()
        )


@pytest.mark.run(after="test_install")
def test_all_services():
    with open("snap/snapcraft.yaml") as file:
        snapcraft = yaml.safe_load(file)

    skip = []

    snap_apps = snapcraft["apps"]
    snap_name = snapcraft['name']

    for app, data in snap_apps.items():
        if not bool(data.get("daemon")) or app in skip:
            continue

        print(f"Running {snap_name}.{app}...")
        subprocess.check_output(
            f"sudo snap start {snap_name}.{app}".split()
        )

        time.sleep(5)
        service = subprocess.check_output(
            f"snap services {snap_name}.{app}".split()
        )
        subprocess.check_output(
            f"sudo snap stop {snap_name}.{app}".split()
        )

        assert "active" in service.decode()
