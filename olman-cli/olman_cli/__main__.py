#! /bin/python3

import argparse

from olman_cli.info import info
from olman_cli.install import install
from olman_cli.remove import remove
from olman_cli.search import search
from olman_cli.update import update

# from .remove import remove


def main():
    main_parser = argparse.ArgumentParser(
        prog="olman",
        description="OpenSCAD Library Manager",
    )
    main_parser.set_defaults(func=lambda x: main_parser.print_help())

    subparsers = main_parser.add_subparsers()

    # update
    update_parser = subparsers.add_parser("update")
    update_parser.set_defaults(func=lambda x: update(update_parser, x))

    # install
    install_parser = subparsers.add_parser("install")
    install_parser.set_defaults(func=lambda x: install(install_parser, x))

    # remove
    remove_parser = subparsers.add_parser("remove")
    remove_parser.set_defaults(func=lambda x: remove(remove_parser, x))

    # search
    search_parser = subparsers.add_parser("search")
    search_parser.set_defaults(func=lambda x: search(search_parser, x))

    # info
    info_parser = subparsers.add_parser("info")
    info_parser.set_defaults(func=lambda x: info(info_parser, x))

    args, other = main_parser.parse_known_args()
    # print(args, other)
    args.func(other)


if __name__ == "__main__":
    main()
