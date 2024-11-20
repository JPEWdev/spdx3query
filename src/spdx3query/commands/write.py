# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from pathlib import Path

from ..cmd import Command, register
from .. import spdx3


@register("write", "Write out SPDX Document")
class Write(Command):
    @classmethod
    def get_args(cls, parser):
        parser.add_argument(
            "--output",
            "-o",
            type=Path,
            help="Output file",
            required=True,
        )
        parser.add_argument(
            "--root",
            "-r",
            help="Root object handle(s)",
            action="append",
            default=[],
        )
        parser.add_argument(
            "--created-by",
            "-c",
            help="Agent creating the document",
            action="append",
            default=[],
            required=True,
        )

    @classmethod
    def handle(cls, args, doc):
        out_doc = doc.copy()

        spdx_doc = spdx3.SpdxDocument()

        for d in out_doc.foreach_type(spdx3.SpdxDocument):
            try:
                out_doc.objects.remove(d)
            except KeyError:
                pass

            for i in d.import_:
                # If this SPDX ID is now provided in the object set, do not add
                # the import
                if out_doc.find_by_id(i.externalSpdxId):
                    continue

                # If the import is already defined, skip it
                if any(
                    i.externalSpdxId == out_i.externalSpdxId
                    for out_i in spdx_doc.import_
                ):
                    continue

                spdx_doc.import_.append(i)

        out_doc.add(spdx_doc)

        spdx_doc.creationInfo = spdx3.CreationInfo()
        spdx_doc.creationInfo

        with args.output.open("w") as f:
            s = spdx3.JSONLDSerializer()
            s.write(out_doc, f)
