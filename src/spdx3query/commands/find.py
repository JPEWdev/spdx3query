# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import re

from ..cmd import Command, register, CommandExit
from .. import spdx3

from .show import show_object


def check_enum(val, enum, desc):
    if val in enum.NAMED_INDIVIDUALS.values():
        return val

    if val not in enum.NAMED_INDIVIDUALS.keys():
        print(f"Unknown {desc} '{val}'. Choose from:")
        print("  " + "\n  ".join(sorted(v for v, _ in enum.valid_values)))
        raise CommandExit(1)

    return getattr(enum, val)


def get_obj_by_handle(doc, handle, typ=None):
    o = doc.find_by_handle(handle)
    if o is None:
        print(f"Unable to find object named '{handle}'")
        raise CommandExit(1)

    if typ is not None:
        if not isinstance(o, typ):
            print(
                f"'{handle}' must be of type {typ.COMPACT_TYPE or typ.TYPE}, but is actually {o.COMPACT_TYPE or o.TYPE}"
            )
            raise CommandExit(1)

    return o


def find_relationships(doc, from_, rel_type, to):
    if rel_type == "-":
        rel_type_iri = None
    else:
        rel_type_iri = check_enum(rel_type, spdx3.RelationshipType, "Relationship Type")

    if from_ is None or from_ == "-":
        from_obj = None
    else:
        from_obj = get_obj_by_handle(doc, from_)

    if to is None or to == "-":
        to_obj = None
    else:
        to_obj = get_obj_by_handle(doc, to)

    return doc.foreach_relationship(from_obj, rel_type_iri, to_obj)


@register("find", "Find elements by property")
class Find(Command):
    @classmethod
    def get_args(cls, parser):
        display_group = parser.add_mutually_exclusive_group()
        display_group.add_argument(
            "--show",
            action="store_true",
            help="Show full objects instead of just handles",
        )
        display_group.add_argument(
            "--count",
            action="store_true",
            help="Only show object count",
        )

        parser.add_argument(
            "--verified-using",
            nargs=2,
            metavar=("ALGORITHM", "HASH"),
            help="Find elements verified by the given hash",
        )
        parser.add_argument(
            "--name",
            help="Find Elements with the element name NAME",
            action="append",
            default=[],
        )
        parser.add_argument(
            "--name-pattern",
            metavar="PATTERN",
            help="Find Elements with element name NAME (regex pattern)",
            action="append",
            default=[],
        )
        parser.add_argument(
            "--external-id",
            nargs=2,
            metavar=("TYPE", "IDENTIFIER"),
            help="Find elements with an external identfier",
            action="append",
            default=[],
        )
        parser.add_argument(
            "--external-id-pattern",
            nargs=2,
            metavar=("TYPE", "PATTERN"),
            help="Find elements with an external identfier (regex pattern)",
            action="append",
            default=[],
        )
        parser.add_argument("--type", help="Type (compact name or IRI)")
        parser.add_argument(
            "--subclass",
            metavar="TYPE",
            help="Type (compact name or IRI) or a subclass of said type",
        )
        parser.add_argument(
            "--references",
            "-f",
            metavar="HANDLE",
            help="Find any object that references the object with handle HANDLE",
        )
        parser.add_argument(
            "--exclude",
            "-x",
            metavar="HANDLE",
            action="append",
            default=[],
            help="Exclude objects with handle HANDLE",
        )

        parser.add_argument(
            "--relationship",
            "-r",
            nargs=3,
            metavar=("FROM", "TYPE", "TO"),
            help="Finds a relationship of type TYPE that relates handle FROM to handle TO. If FROM, TYPE, or TO are '-', they will be ignored when matching",
        )
        parser.add_argument(
            "--to",
            nargs=2,
            metavar=("TYPE", "TO"),
            help="Find Elements in the 'from' side of a Relationship type TYPE where handle TO is the to field",
            dest="rel_to",
        )
        parser.add_argument(
            "--from",
            nargs=2,
            metavar=("FROM", "TYPE"),
            help="Find Elments in the 'to' side of a Relationship type TYPE where handle FROM is in the from field",
            dest="rel_from",
        )

    @classmethod
    def handle(self, args, doc):
        final = set(doc.foreach())

        if args.type:
            final &= set(doc.foreach_type(args.type, match_subclass=False))

        if args.subclass:
            final &= set(doc.foreach_type(args.subclass, match_subclass=True))

        if args.verified_using:
            objs = set()

            algo, val = args.verified_using
            algo_iri = check_enum(algo, spdx3.HashAlgoritm, "hash algorithm")

            for o in doc.foreach_type(spdx3.Element, match_subclass=True):
                for v in o.verifiedUsing:
                    if isinstance(v, spdx3.Hash):
                        if v.algorithm == algo_iri and v.hashValue == val:
                            objs.add(o)

            final &= objs

        for name in args.name:
            objs = set()
            for o in doc.foreach_type(spdx3.Element, match_subclass=True):
                if o.name == name:
                    objs.add(o)

            final &= objs

        for pattern in args.name_pattern:
            objs = set()
            for o in doc.foreach_type(spdx3.Element, match_subclass=True):
                if o.name is None:
                    continue

                if re.search(pattern, o.name):
                    objs.add(o)

            final &= objs

        if args.references:
            objs = set()
            ref_obj = get_obj_by_handle(doc, args.references)
            for o in doc.foreach():
                if ref_obj in o.iter_objects():
                    objs.add(o)
            final &= objs

        for ext_id in args.external_id:
            ext_id_type, ident = ext_id
            final &= set(
                doc.foreach_external_id(
                    check_enum(
                        ext_id_type,
                        spdx3.ExternalIdentifierType,
                        "external identifier type",
                    ),
                    lambda i: i == ident,
                )
            )

        for ext_id in args.external_id_pattern:
            ext_id_type, pattern = ext_id
            final &= set(
                doc.foreach_external_id(
                    check_enum(
                        ext_id_type,
                        spdx3.ExternalIdentifierType,
                        "external identifier type",
                    ),
                    lambda i: re.search(pattern, i),
                )
            )

        if args.relationship:
            final &= set(find_relationships(doc, *args.relationship))

        if args.rel_to:
            objs = set()
            for rel in find_relationships(doc, "-", *args.rel_to):
                objs.add(rel.from_)

            final &= objs

        if args.rel_from:
            objs = set()
            for rel in find_relationships(doc, *args.rel_from, "-"):
                objs |= set(rel.to)

            final &= objs

        remove = set()
        for r in args.exclude:
            remove.add(get_obj_by_handle(doc, r))

        final -= remove

        if args.count:
            print(f"Found {len(final)} object(s)")
        else:
            print(f"Found {len(final)} object(s):")
            for o in sorted(list(final)):
                show_object(o, args.show)
        return 0
