#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import argparse
import shlex
import time
import traceback
from pathlib import Path

from .version import VERSION
from .cmd import COMMANDS, CommandExit
from .name import get_object_handle
from . import spdx3

EPILOG = """
"""


class ArgumentError(Exception):
    pass


class ShellExit(Exception):
    pass


class InteractiveParser(argparse.ArgumentParser):
    def error(self, message):
        raise ArgumentError(message)

    def exit(self, *args, **kwargs):
        raise ArgumentError()


def add_commands(subparser):
    for name, desc, c in COMMANDS:
        p = subparser.add_parser(name, help=desc)
        c.get_args(p)
        p.set_defaults(func=c.handle)


class Document(spdx3.SHACLDocument):
    def create_index(self):
        self.obj_by_handle = {}
        super().create_index()

    def add_index(self, obj):
        super().add_index(obj)
        handle = get_object_handle(obj)
        obj._metadata["handle"] = handle
        if handle in self.obj_by_handle and self.obj_by_handle[handle] is not obj:
            print(f"Warning: handle '{handle}' is not unique")
        self.obj_by_handle[handle] = obj

    def count(self):
        return len(self.obj_by_handle)

    def find_by_handle(self, handle):
        if handle in self.obj_by_handle:
            return self.obj_by_handle[handle]
        return None

    def foreach_relationship(self, from_, typ, to):
        for rel in self.foreach_type(spdx3.Relationship, subclass=True):
            if typ is not None and rel.relationshipType != typ:
                continue

            if to is not None and to not in rel.to:
                continue

            if from_ is not None and rel.from_ != from_:
                continue

            yield rel

    def foreach_relationship_from(self, from_, typ):
        for rel in self.foreach_relationship(from_, typ, None):
            for o in rel.to:
                yield o

    def foreach_relationship_to(self, typ, to):
        for rel in self.foreach_relationship(None, typ, to):
            yield rel.from_

    def foreach_external_id(self, type_iri, check_id, obj_type=spdx3.Element):
        for o in self.foreach_type(obj_type, subclass=True):
            for v in o.externalIdentifier:
                if isinstance(v, spdx3.ExternalIdentifier):
                    if v.externalIdentifierType != type_iri:
                        continue

                    if check_id(v.identifier):
                        yield o


def handle_interactive(args, doc):
    try:
        import readline  # noqa
    except ImportError:
        pass

    def handle_help(args, doc):
        nonlocal parser
        parser.print_help()
        return 0

    def handle_quit(args, doc):
        raise ShellExit()

    def handle_clear(args, doc):
        print("\x1b[2J\x1b[H", end="")

    parser = InteractiveParser(add_help=False, epilog=EPILOG)
    command_subparser = parser.add_subparsers(
        title="command",
        description="Command to execute",
        metavar="COMMAND",
        required=True,
    )

    help_parser = command_subparser.add_parser("help", help="Show help", add_help=False)
    help_parser.set_defaults(func=handle_help)

    quit_parser = command_subparser.add_parser("quit", help="Quit", add_help=False)
    quit_parser.set_defaults(func=handle_quit)

    clear_parser = command_subparser.add_parser(
        "clear", help="Clear screen", add_help=False
    )
    clear_parser.set_defaults(func=handle_clear)

    add_commands(command_subparser)

    while True:
        try:
            cmd = input("> ")
            c = shlex.split(cmd)
            if not c:
                continue

            cmd_args = parser.parse_args(c)

            cmd_args.func(cmd_args, doc)

        except KeyboardInterrupt:
            print("Interrupted")
        except ArgumentError as e:
            print(str(e))
        except CommandExit:
            pass
        except ShellExit:
            return 0
        except Exception:
            traceback.print_exc()


def main(args=None):
    parser = argparse.ArgumentParser(description="Query SPDX 3 files", epilog=EPILOG)
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=VERSION,
    )
    parser.add_argument(
        "--input",
        "-i",
        help="Input SPDX 3 file(s)",
        type=Path,
        action="append",
        default=[],
    )

    command_subparser = parser.add_subparsers(
        title="command",
        description="Command to execute",
        metavar="COMMAND",
        required=True,
    )

    interactive_parser = command_subparser.add_parser(
        "interactive",
        help="Interactive queries",
    )
    interactive_parser.set_defaults(func=handle_interactive)

    add_commands(command_subparser)

    args = parser.parse_args(args)

    d = spdx3.JSONLDDeserializer()
    doc = Document()
    start = time.time()
    for i in args.input:
        with i.open("rb") as f:
            d.read(f, doc)
    elapsed = time.time() - start

    print(f"Loaded {doc.count()} objects in {elapsed:.2f}s")

    try:
        return args.func(args, doc)
    except CommandExit as e:
        return e.exit_code
