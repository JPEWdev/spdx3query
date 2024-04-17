# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from ..cmd import Command, register
from .. import spdx3


@register("load", "Load SPDX 3 Data File")
class Load(Command):
    @classmethod
    def get_args(cls, parser):
        parser.add_argument(
            "input",
            help="Input SPDX 3 file(s)",
            type=Path,
            nargs="+",
        )

    @classmethod
    def handle(self, args, doc):
        d = spdx3.JSONLDDeserializer()
        for i in args.input:
            with i.open("rb") as f:
                d.read(f, doc)
        return 0
