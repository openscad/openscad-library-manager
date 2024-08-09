import argparse
import json
import logging
import tempfile
import time
import tomllib
from concurrent.futures import ProcessPoolExecutor as ppe
from pathlib import Path
from subprocess import run

from olman_models import Manifest
from olman_vcs_utils import getRepoZipLink
from olman_version_utils import version_key

ACCEPTED_REPOSITORIES_FILENAME = "accepted_repositories.txt"
INDEX_FILENAME = "remote_index.json"
MANIFEST_FILENAME = "manifest.toml"
INDEX_SOURCE_SEPARATOR = "||"
RECORD_SEP = ", "

DEFAULT_VERBOSITY_LEVEL = 0
VERBOSITY_LEVELS = [
    logging.WARN,  # 0
    logging.INFO,  # 1
    logging.DEBUG,  # 2
]


class Utils:
    @staticmethod
    def error_exit(msg: str):
        logging.error(msg=msg)
        exit(1)


def process_repo(repo_url: str, lib_name: str) -> list:
    logger = logging.getLogger(lib_name)
    logger.debug("Creating temp dir")
    with tempfile.TemporaryDirectory() as repo_directory:
        logger.info("Cloning the repo")
        run(
            ["git", "clone", "--depth", "1", repo_url, repo_directory],
            cwd=repo_directory,
            capture_output=True,
            check=True,
        )

        # Get all tags in library repo
        logger.info("Fetching tags")
        run(
            ["git", "fetch", "--tags"],
            cwd=repo_directory,
            capture_output=True,
            check=True,
        )

        logger.info("Getting the tag SHAs")
        proc = run(
            ["git", "show-ref", "--tags"],
            cwd=repo_directory,
            capture_output=True,
            text=True,
            check=True,
        )

        # get tag name from here
        # 60a7d86cb43d087855dd001c547ed1f82f617387 refs/tags/1.0.0
        tag_shas = [
            commit_tag.split()[0] for commit_tag in proc.stdout.strip().split("\n")
        ]
        logger.debug(f"{tag_shas = }")

        # Parse manifest of every tag
        entries = []
        for tag_sha in tag_shas:
            logger.info(f"Checking out SHA {tag_sha}")
            run(
                ["git", "checkout", tag_sha],
                cwd=repo_directory,
                capture_output=True,
                check=True,
            )

            # Get library info from manifest
            logger.info("Parsing manifest")
            manifest_path = Path(repo_directory) / MANIFEST_FILENAME
            with open(manifest_path, "rb") as f:
                manifest_data = tomllib.load(f)

            # Validate all fields
            manifest = Manifest(**manifest_data)

            # Check name
            logger.info("Checking name")
            if manifest.library.name != lib_name:
                logging.warning(f"tag {tag_sha} in {repo_url} contains invalid name")
                continue

            # TODO: check if tag name matches version

            # Add to list
            logging.info("Adding library to list")
            entries.append(
                {
                    "manifest": manifest.model_dump(),
                    "download_link": getRepoZipLink(repo_url, sha=tag_sha),
                }
            )

    logger.debug("entries:")
    logger.debug(entries)
    return entries


def main():
    parser = argparse.ArgumentParser("index_generator")

    parser.add_argument(
        "-a",
        "--accepted-repositories",
        required=True,
        help="Path to the accepted repositories file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to output file.",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        required=False,
        default=None,
        type=int,
        help="Number of parallel jobs.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=DEFAULT_VERBOSITY_LEVEL,
        help="Increase verbosity level",
    )

    args = parser.parse_args()
    accepted_repositories_loc = args.accepted_repositories
    output_loc = args.output

    logging.basicConfig(level=VERBOSITY_LEVELS[args.verbosity])
    logging.debug(f"{args = }")

    accepted_repositories_path = Path(accepted_repositories_loc)
    index_file_path = Path(output_loc)
    logging.debug(f"{accepted_repositories_path = }")
    logging.debug(f"{index_file_path = }")

    records = []
    logging.debug("Creating process pool")
    logging.info("Opening accepted repositories file")
    with ppe(args.jobs) as p, open(accepted_repositories_path, "r") as f_arp:
        logging.debug("Processing lines")
        while line := f_arp.readline():
            line = line.strip()
            logging.debug(f"{line = }")

            if line.startswith("#"):
                logging.debug("Skipping")
                continue

            repo_url, lib_name = line.split(INDEX_SOURCE_SEPARATOR)
            logging.debug(f"{repo_url = }")
            logging.debug(f"{lib_name = }")

            # parse repo
            logging.info(f"Processing repo: {repo_url}")
            future = p.submit(
                process_repo,
                repo_url=repo_url,
                lib_name=lib_name,
            )
            future.add_done_callback(lambda x: records.extend(x.result()))

    # TODO: correctly sort versions with libversion
    records.sort(
        key=lambda x: (
            x["manifest"]["library"]["name"],
            version_key(x["manifest"]["library"]["version"]),
        )
    )

    with open(index_file_path, "w") as f:
        json.dump(
            {
                "libraries": records,
                "timestamp": time.time(),
            },
            f,
            sort_keys=True,
        )


if __name__ == "__main__":
    main()
