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
from .name import get_handle
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


class Document(spdx3.SHACLObjectSet):
    def __init__(self, handle_terms):
        super().__init__()
        self.handle_terms = handle_terms

    def copy(self):
        doc = self.__class__(self.handle_terms)
        doc.objects = self.objects.copy()
        doc.create_index()
        return doc

    def create_index(self):
        self.obj_by_handle = {}
        self.type_handle_map = {}
        super().create_index()

    def add_index(self, obj):
        super().add_index(obj)
        if obj._id and not spdx3.is_blank_node(obj._id):
            handle_str = obj._id
            prefix = None
        else:
            handle_str = obj.TYPE + " " + hex(len(self.obj_by_handle))
            prefix = "LOCAL"

        handle = get_handle(handle_str, self.handle_terms, prefix=prefix)
        obj._metadata["handle"] = handle
        if handle in self.obj_by_handle and self.obj_by_handle[handle] is not obj:
            print(
                f"Warning: handle '{handle}' ({handle_str}) is not unique. Conflicts with {self.obj_by_handle[handle]._id}"
            )
        self.obj_by_handle[handle] = obj

        if obj.TYPE not in spdx3.SHACLObject.CLASSES:
            type_handle = get_handle(obj.TYPE)
            obj._metadata["type_handle"] = type_handle
            self.type_handle_map[type_handle] = obj.TYPE

    def count(self):
        return len(self.obj_by_handle)

    def foreach_type(self, typ, **kwargs):
        if typ in self.type_handle_map:
            typ = self.type_handle_map[typ]
        return super().foreach_type(typ, **kwargs)

    def find_by_handle(self, handle):
        if handle in self.obj_by_handle:
            return self.obj_by_handle[handle]
        return None

    def foreach_relationship(self, from_, typ, to):
        for rel in self.foreach_type(spdx3.Relationship, match_subclass=True):
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
        for o in self.foreach_type(obj_type, match_subclass=True):
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
    parser.add_argument(
        "--handle-terms",
        help="Number of handle terms. Default is %(default)s. Larger datasets may require more terms to keep unique handles",
        type=int,
        default=3,
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
    doc = Document(args.handle_terms)
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
