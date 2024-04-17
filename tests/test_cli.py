# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import subprocess


def test_help():
    subprocess.run(["spdx3query", "--help"], check=True)
