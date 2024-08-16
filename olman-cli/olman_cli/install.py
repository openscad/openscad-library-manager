import argparse

import olman_client

from .utils import ref_split


def install(parser: argparse.ArgumentParser, args: list[str]):
    parser.add_argument(
        "ref",
        nargs="+",
    )
    parser.add_argument(
        "-f",
        "--force",
    )
    args = parser.parse_args(args)

    refs = args.ref

    for ref in refs:
        name, constraint = ref_split(ref)

        if constraint == "":
            constraint = ">=0.0.0"

        olman_client.install(name, constraint, force=args.force)
