# Copyright (C) Lutra Consulting Limited
#
# SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-MerginMaps-Commercial


def get_version():
    return "2023.3.0"


def get_git_hash():
    import subprocess

    return (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
        .decode("ascii")
        .strip()
    )
