# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from ..cmd import Command, register


@register("info", "Data Info")
class Info(Command):
    @classmethod
    def get_args(cls, parser):
        parser.add_argument(
            "--show-missing",
            action="store_true",
            help="Show missing SPDX IDs",
        )

    @classmethod
    def handle(self, args, doc):
        print()
        missing = doc.link()
        print(f"Object count:     {doc.count()}")
        print(f"Missing SPDX IDs: {len(missing)}")
        if args.show_missing:
            for m in missing:
                print(f"  {m}")
        return 0
