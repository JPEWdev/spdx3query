# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from ..cmd import Command, register
from .. import spdx3


def show_object(obj, full=True, *, elide=True):
    def print_obj(o):
        print(f"{o.COMPACT_TYPE or o.TYPE} ", end="")
        if type_handle := o._metadata.get("type_handle", None):
            print(f"({type_handle}) ", end="")
        print(f"- '{o._metadata['handle']}'")

    def print_value(val, depth, prefix):
        if isinstance(val, spdx3.SHACLObject):
            print(prefix, end="")
            if not val._id:
                print_object_props(val, depth + 1)
            else:
                print_obj(val)
        elif isinstance(val, spdx3.ListProxy):
            if len(val) == 0:
                if not elide:
                    print(f"{prefix}[]")
                return

            print(prefix, end="")
            if len(val) == 1:
                print_value(val[0], depth, "")
            else:
                print("[")
                for v in val:
                    print_value(v, depth + 1, "  " * (depth + 2))
                print("  " * (depth + 1) + "]")
        else:
            if val is None:
                if not elide:
                    print(prefix)
                return

            print(prefix, end="")
            if isinstance(val, str):
                print(repr(val))
            else:
                print(val)

    def print_object_props(o, depth=0):
        print_obj(o)
        for _, iri, compact in o.property_keys():
            print_value(o[iri], depth, "  " * (depth + 1) + (compact or iri) + ": ")

    if full:
        print()
        print_object_props(obj)
    else:
        print_obj(obj)


@register("show", "Show Elements")
class Show(Command):
    @classmethod
    def get_args(cls, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Show all fields, even if empty",
        )
        parser.add_argument(
            "handle",
            nargs="+",
            help="Show element(s) with handle 'HANDLE'",
        )

    @classmethod
    def handle(self, args, doc):
        for handle in args.handle:
            print()
            o = doc.find_by_handle(handle)
            if o is None:
                o = doc.find_by_id(handle)
            if o is None:
                print(f"No object named '{handle}' found")
                return 1

            show_object(o, elide=not args.all)

        return 0
