import argparse

from olman_client import api


def update(parser: argparse.ArgumentParser, args: list[str]):
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
    )
    args = parser.parse_args(args)

    print("Updating remote index...")
    status = api.update(args.force)
    if status:
        print("Updated")

    else:
        print("Did not update")
