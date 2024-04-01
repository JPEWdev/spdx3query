# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from ..cmd import Command, register
from .. import spdx3

from .show import show_object


@register("vuln", "Vulnerability information")
class Vuln(Command):
    @classmethod
    def get_args(cls, parser):
        commands = parser.add_subparsers(
            title="command",
            description="Command to execute",
            metavar="COMMAND",
            required=True,
        )

        affected_by_command = commands.add_parser(
            "affected-by",
            help="Find elements affected by a CVE. The CVE must be in the SPDX data",
        )
        affected_by_command.add_argument(
            "--show",
            action="store_true",
            help="Show full objects instead of just names",
        )
        affected_by_command.add_argument(
            "cve",
            metavar="CVE",
            nargs="+",
            help="CVE to check",
        )
        affected_by_command.set_defaults(func=cls.handle_affected_by)

    @classmethod
    def handle(cls, args, doc):
        pass

    @classmethod
    def handle_affected_by(cls, args, doc):
        objs = set()

        for c in args.cve:
            cves = set(
                doc.foreach_external_id(
                    spdx3.ExternalIdentifierType.cve,
                    lambda i: i == c,
                    obj_type=spdx3.security_Vulnerability,
                )
            )

            if not cves:
                print(f"Unable to find {c}")
                return 1

            for cve in cves:
                objs |= set(
                    doc.foreach_relationship_to(
                        spdx3.RelationshipType.hasAssociatedVulnerability, cve
                    )
                )

        for obj in objs:
            show_object(obj, args.show)
