import argparse
from pprint import pprint

from olman_client import api


def info(parser: argparse.ArgumentParser, args: list[str]):
    parser.add_argument(
        "name",
    )
    args = parser.parse_args(args)

    name = args.name

    pprint(api.info(name))
