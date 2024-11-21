# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from ..cmd import Command, register
from .. import spdx3


def show_object(obj, full=True, *, elide=True, _prefix=""):
    def print_obj(o, *, obj_prefix=""):
        print(f"{obj_prefix}{o.COMPACT_TYPE or o.TYPE} ", end="")
        if type_handle := o._metadata.get("type_handle", None):
            print(f"({type_handle}) ", end="")
        print(f"- '{o._metadata['handle']}'")

    def print_value(val, depth, prefix, *, obj_prefix=""):
        if isinstance(val, spdx3.SHACLObject):
            print(prefix, end="")
            if not val._id:
                print_object_props(val, depth + 1, obj_prefix=obj_prefix)
            else:
                print_obj(val, obj_prefix=obj_prefix)
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
                for idx, v in enumerate(val):
                    print_value(v, depth + 1, "  " * (depth + 2) + f"[{idx}]: ")
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

    def print_object_props(o, depth=0, *, obj_prefix=""):
        print_obj(o, obj_prefix=obj_prefix)
        for _, iri, compact in o.property_keys():
            print_value(o[iri], depth, "  " * (depth + 1) + (compact or iri) + ": ")

    if isinstance(obj, (list, spdx3.ListProxy)):
        for idx, o in enumerate(obj):
            show_object(o, full=full, elide=elide, _prefix=f"[{idx}]: ")
        return

    if not isinstance(obj, spdx3.SHACLObject):
        print(repr(obj))
        return

    if full:
        print()
        print_object_props(obj, obj_prefix=_prefix)
    else:
        print_obj(obj, obj_prefix=_prefix)


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
            metavar="HANDLE[.PATH]",
            nargs="*",
            help="Show element(s) with handle 'HANDLE[.PATH]'. If HANDLE is omitted, the current focus object is used",
            default=["."],
        )

    @classmethod
    def handle(self, args, doc):
        for handle in args.handle:
            try:
                o = doc.find_by_path(handle)
            except (AttributeError, IndexError) as e:
                print(e)
                return 1

            if o is None:
                print("No object at '{handle}' found")
                return 1

            show_object(o, elide=not args.all)

        return 0
