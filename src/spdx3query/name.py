# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import hashlib
from pathlib import Path

THIS_DIR = Path(__file__).parent

WORDLIST = (THIS_DIR / "wordlist.txt").open("r").read().split()


def get_object_handle(o, n=3):
    prepend = []
    if o._id:
        _id = o._id
    else:
        _id = hex(id(o))
        prepend.append("TEMP")

    h = int.from_bytes(hashlib.md5(_id.encode("utf-8")).digest(), "big")

    words = []
    for i in range(n):
        words.append(WORDLIST[h % len(WORDLIST)])
        h = h // len(WORDLIST)

    words.reverse()
    return "-".join(prepend + words)
