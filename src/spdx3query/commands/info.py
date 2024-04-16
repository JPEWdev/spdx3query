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
        parser.add_argument(
            "--show-types",
            action="store_true",
            help="Show types found in Document",
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
        print(f"Type count:       {len(doc.obj_by_type)}")
        if args.show_types:
            for t in sorted(list(doc.obj_by_type.keys())):
                print(f"  {t}", end="")
                for k, v in doc.type_handle_map.items():
                    if t == v:
                        print(f" ({k})", end="")
                print()
        return 0
