# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import hashlib
from pathlib import Path

THIS_DIR = Path(__file__).parent

WORDLIST = (THIS_DIR / "wordlist.txt").open("r").read().split()


def get_handle(s, n=3, *, prefix=None):
    h = int.from_bytes(hashlib.md5(s.encode("utf-8")).digest(), "big")

    words = []
    for i in range(n):
        words.append(WORDLIST[h % len(WORDLIST)])
        h = h // len(WORDLIST)

    if prefix:
        words.append(prefix)

    words.reverse()
    return "-".join(words)
