import argparse

from olman_client import api


def remove(parser: argparse.ArgumentParser, args: list[str]):
    parser.add_argument(
        "name",
        nargs="+",
    )
    args = parser.parse_args(args)

    names = args.name

    for name in names:
        print(f"Removing {name}")
        api.remove(name)

    print(f"Removed {len(names)} libraries: {names}")
