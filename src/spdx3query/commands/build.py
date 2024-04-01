# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from ..cmd import Command, register
from .. import spdx3

from .show import show_object
from .find import get_obj_by_handle


@register("build", "Build Information")
class Build(Command):
    @classmethod
    def get_args(cls, parser):
        commands = parser.add_subparsers(
            title="command",
            description="Command to execute",
            metavar="COMMAND",
            required=True,
        )

        chain_command = commands.add_parser(
            "chain",
            help="Show build chain between two builds",
        )
        chain_command.add_argument(
            "--show",
            action="store_true",
            help="Show full objects instead of just names",
        )
        chain_command.add_argument("parent", help="Parent build")
        chain_command.add_argument("child", help="Child build")
        chain_command.add_argument(
            "--shortest", help="Only show shortest chain", action="store_true"
        )
        chain_command.add_argument(
            "--longest", help="Only show longest chain", action="store_true"
        )
        chain_command.set_defaults(func=cls.handle_chain)

    @classmethod
    def handle(self, args, doc):
        return 0

    @classmethod
    def handle_chain(cls, args, doc):
        def search(obj, child, visited=None):
            if visited is None:
                visited = set()

            if obj in visited:
                return

            visited.add(obj)

            for rel in doc.foreach_relationship(
                None,
                spdx3.RelationshipType.dependsOn,
                obj,
            ):
                if child is rel.from_:
                    yield [obj, child]

                if not isinstance(rel.from_, spdx3.build_Build):
                    continue

                for chain in search(rel.from_, child, visited):
                    yield [obj] + chain

            for out_rel in doc.foreach_relationship(
                obj, spdx3.RelationshipType.hasOutputs, None
            ):
                for out in out_rel.to:
                    for in_rel in doc.foreach_relationship(
                        None, spdx3.RelationshipType.hasInputs, out
                    ):
                        if child is in_rel.from_:
                            yield [obj, out, child]

                        for chain in search(in_rel.from_, child, visited):
                            yield [obj, out] + chain

        def get_name(o):
            name = o._metadata["handle"]
            if isinstance(o, spdx3.build_Build):
                return name
            return f"[{name}]"

        parent = get_obj_by_handle(doc, args.parent, spdx3.build_Build)
        child = get_obj_by_handle(doc, args.child, spdx3.build_Build)

        chains = sorted(search(parent, child), key=lambda x: (len(x), x))
        print(f"Found {len(chains)} chains:")
        if args.shortest and chains:
            chains = chains[:1]
        if args.longest and chains:
            chains = chains[-1:]
        for idx, chain in enumerate(chains):
            if args.show:
                print()
                print(f"CHAIN {idx + 1}:")
                for o in chain:
                    print()
                    show_object(o)
            else:
                print(f"{idx + 1}: " + " -> ".join(get_name(o) for o in chain))
        return 0
