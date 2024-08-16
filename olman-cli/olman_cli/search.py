import argparse
from pprint import pprint

from olman_client import api

from .utils import ref_split


def search(parser: argparse.ArgumentParser, args: list[str]):
    parser.add_argument(
        "ref",
    )
    args = parser.parse_args(args)

    ref = args.ref

    name, constraint = ref_split(ref)

    pprint(api.search(name, constraint))
