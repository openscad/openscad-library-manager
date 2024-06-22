# Standard libraries
import argparse
import json
import logging
import subprocess
import tempfile
import tomllib
from enum import StrEnum
from pathlib import Path
from pprint import pformat
from textwrap import indent as tw_indent
from urllib.parse import ParseResult, urlparse

# External libraries
import requests
import unidiff

# ---------------------------------------------------------------------------- #

MANIFEST_FILENAME = "manifest.toml"
INDEX_SOURCE_SEPARATOR = "||"
OUTPUT_INDENTATION = 2

DEFAULT_VERBOSITY_LEVEL = 0
VERBOSITY_LEVELS = [
    logging.WARN,  # 0
    logging.INFO,  # 1
    logging.DEBUG,  # 2
]

SUPPORTED_HOSTS = [
    "bitbucket.org",
    # "git.antares.id",
    "github.com",
    "gitlab.com",
]

OFFICIAL_ORGANIZATIONS = [
    "github.com/openscad",
]

VALID_REPO_TYPES = [
    "OpenSCAD",
    "Partner",
    "Contributed",
]


class Utils:
    @staticmethod
    def url_accessible(url: ParseResult) -> bool:
        """Check if a given URL is accessible with a GET request or not.

        Parameters
        ----------
        url : ParseResult
            URL to be checked

        Returns
        -------
        bool
            True if the response is 200 (OK). False otherwise.
        """
        return requests.get(url.geturl()).ok

    @staticmethod
    def error_exit(msg: str):
        logging.error(msg=msg)
        # print(f"ERROR: {msg}", file=stderr)
        exit(1)

    @staticmethod
    def normalize_git_url(raw_url: ParseResult | str) -> ParseResult:
        """Transforms the GIT repo URL into a normalized format.
        Removing trailing slashes and adding .git postfix.

        Parameters
        ----------
        raw_url : ParseResult | str
            URL to be normalized

        Returns
        -------
        ParseResult
            Normalized GIT repo URL
        """
        if isinstance(raw_url, str):
            raw_url = urlparse(raw_url)

        normalized_url = raw_url._replace(path=raw_url.path.rstrip("/"))

        if normalized_url.path == "":
            normalized_url = normalized_url._replace(path="/")

        elif not normalized_url.path.endswith(".git"):
            normalized_url = normalized_url._replace(path=normalized_url.path + ".git")

        normalized_url = urlparse(
            f"https://{normalized_url.hostname}{normalized_url.path}"
        )
        return normalized_url

    @staticmethod
    def url_is_under(url: ParseResult, candidates: str | list[str]) -> bool:
        """Check if the URL is under any of the given candidates.

        Parameters
        ----------
        url : ParseResult
            URL to check
        candidates : str | list[str]
            List of URLs to check against.

        Returns
        -------
        bool
            True if the URL is under any of the candidates.
        """
        if isinstance(candidates, str):
            candidates = [candidates]

        for cand in candidates:
            if not cand.endswith("/"):
                cand = cand + "/"

            cand_url = urlparse(f"https://{cand}")

            cand_parts = [
                cand_url.hostname,
                *(cand_url.path.strip("/").split("/") if cand_url.path != "/" else []),
            ]
            url_parts = [url.hostname, *url.path.strip("/").split("/")]

            if cand_parts == url_parts[: len(cand_parts)]:
                return True

        return False

    @staticmethod
    def indent(text: str, spaces: int = 2) -> str:
        return "\n" + tw_indent(text=text, prefix=" " * spaces)


class MyEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__


class Submission:
    # url: str
    # normalized_url: str
    # repository_name: str
    # official: str
    # tag: str # latest tag
    # name: str
    # index_entry: str
    def __init__(self, submission_url: str, list_path: Path):
        logging.info("Creating Submission")
        logging.debug(f"{submission_url = }")
        logging.debug(f"{list_path = }")

        # normalize and validate URL
        logging.info("Parsing submission URL")
        url_obj = urlparse(submission_url)

        # check if URL is accessible
        logging.info("Checking the URL accessibility")
        if not Utils.url_accessible(url_obj):
            Utils.error_exit("Unable to load submission URL. Is the repository public?")

        # normalize url
        logging.info("Normalizing URL")
        normalized_url = Utils.normalize_git_url(url_obj)
        logging.debug(f"normalized_url: {normalized_url.geturl()}")

        # Check if url is from a supported Git host
        logging.info("Checking URL Git host")
        if not Utils.url_is_under(normalized_url, SUPPORTED_HOSTS):
            Utils.error_exit(
                f"{normalized_url.hostname} is not currently supported as a Git hosting website."
            )

        # Check if URL is a Git repository
        logging.info("Checking if the URL points to a Git repository")
        if (
            subprocess.run(
                ["git", "ls-remote", normalized_url.geturl()],
                capture_output=True,
            ).returncode
            != 0
        ):
            Utils.error_exit(
                f"Submission URL ({normalized_url.geturl()}) is not a Git clone URL"
            )

        self.url = submission_url
        self.normalized_url = normalized_url.geturl()
        self.repository_name = Path(normalized_url.path).stem
        logging.debug(f"url: {self.url}")
        logging.debug(f"normalized_url: {self.normalized_url}")
        logging.debug(f"repository_name: {self.repository_name}")

        logging.info("Checking if the URL is already in the list")
        logging.info("Opening list file")
        with open(list_path, "r") as list_file:
            for list_line in list_file.readlines():
                normalized_list_url = Utils.normalize_git_url(list_line)
                logging.debug(f"{list_line = }")
                logging.debug(f"{normalized_list_url = }")

                if normalized_url == normalized_list_url:
                    Utils.error_exit("URL is already in the list")

        logging.info("Checking if the URL is from an official OpenSCAD organization")
        self.official = Utils.url_is_under(normalized_url, OFFICIAL_ORGANIZATIONS)
        logging.debug(f"official: {self.official}")

        logging.info("Processing the submission repository")
        self._parse_submission_repo()

    def _parse_submission_repo(self):
        with tempfile.TemporaryDirectory() as submission_repo_directory:
            logging.info("Cloning the submission repository")
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    self.normalized_url,
                    submission_repo_directory,
                ],
                cwd=submission_repo_directory,
                capture_output=True,
                check=True,
            )

            # Determine latest tag name in submission repo
            logging.info("Fetching the repository's tags")
            subprocess.run(
                ["git", "fetch", "--tags"],
                cwd=submission_repo_directory,
                capture_output=True,
                check=True,
            )

            logging.info("Getting the repository's latest tag SHA")
            proc = subprocess.run(
                ["git", "rev-list", "--tags", "--max-count=1"],
                cwd=submission_repo_directory,
                capture_output=True,
                text=True,
                check=True,
            )
            tag_sha = proc.stdout.strip()
            logging.debug(f"{tag_sha = }")

            if tag_sha == "":
                Utils.error_exit("The repository has no tags.")

            logging.info("Getting the repository's latest tag name")
            proc = subprocess.run(
                ["git", "describe", "--tags", tag_sha],
                cwd=submission_repo_directory,
                capture_output=True,
                text=True,
                check=True,
            )
            self.tag = proc.stdout.strip()
            logging.debug(f"tag: {self.tag}")

            # Checkout latest tag
            logging.info("Checking out the tag's commit")
            subprocess.run(
                ["git", "checkout", self.tag],
                cwd=submission_repo_directory,
                capture_output=True,
                check=True,
            )

            # Get submission library name.
            # It is necessary to record this in the index source entry because
            #   the library is locked to this name.
            logging.info("Opening the manifest")
            manifest_path = Path(submission_repo_directory) / MANIFEST_FILENAME
            with open(manifest_path, "rb") as f:
                manifest_data = tomllib.load(f, parse_float=lambda x: x)
                logging.debug("manifest_data:")
                logging.debug(Utils.indent(pformat(manifest_data)))

            # # TODO: validate manifest here
            logging.info("Validating the manifest")
            # manifest_data: dict

            logging.info("Getting manifest information")
            self.name = manifest_data["library"]["name"]
            self.index_entry = INDEX_SOURCE_SEPARATOR.join(
                (self.normalized_url, self.name)
            )
            logging.debug(f"name: {self.name}")
            logging.debug("Submission index_entry:")
            logging.debug(Utils.indent(self.index_entry))


class SubmissionRequest:  # pull request
    # type: str
    # submissions: list[Submission]
    # index_entry: str
    def __init__(self, diff_path: Path, list_path: Path) -> None:
        logging.info("Creating SubmissionRequest")
        logging.debug(f"{diff_path = }")
        logging.debug(f"{list_path = }")

        # Read PR diff
        logging.info("Opening diff file")
        with open(diff_path, encoding="utf-8") as diff_file:
            raw_diff_data = diff_file.read()
            logging.debug("raw_diff_data:")
            logging.debug(Utils.indent(raw_diff_data))

        # Check if the PR has removed the final newline from a file, which would
        #   cause a spurious diff for the next PR if merged.
        if raw_diff_data.endswith("\\ No newline at end of file\n"):
            Utils.error_exit(
                "Pull request removes newline from the end of a file.\n"
                "Please add a blank line to the end of the file."
            )

        logging.info("Parsing diff")
        diffs = unidiff.PatchSet(raw_diff_data)

        logging.debug(f"{len(diffs) = }")
        logging.debug(f"{diffs[0].source_file = }")
        logging.debug(f"{diffs[0].target_file = }")
        if (
            (len(diffs) != 1)
            or (Path(diffs[0].source_file).name != list_path.name)
            or (Path(diffs[0].target_file).name != list_path.name)
        ):
            Utils.error_exit("Not a library manager submission.")

        additions = 0
        deletions = 0
        submission_urls = []

        logging.info("Processing diff lines")
        for hunk in diffs[0]:
            for raw_diff_line in str(hunk).splitlines():
                diff_line = raw_diff_line.lstrip()
                logging.debug(f"{diff_line = }")

                if diff_line.startswith("+"):
                    additions += 1
                    submission_urls.append(diff_line[1:])
                    logging.debug("  addition")
                    logging.debug(f"Submission URL: {diff_line[1:]}")

                elif diff_line.startswith("-"):
                    deletions += 1
                    logging.debug("  deletion")

                else:
                    continue
        logging.debug(f"{additions = }")
        logging.debug(f"{deletions = }")

        logging.info("Determining submission type")
        if additions == 0 and deletions == 0:
            self.type = "other"

        elif additions > 0 and deletions == 0:
            self.type = "addition"

        elif additions == 0 and deletions > 0:
            self.type = "removal"

        else:
            self.type = "modification"
        logging.debug(f"type : {self.type}")

        # Parse submission urls
        logging.info("Parsing submission URLs")
        self.submissions = [
            Submission(submission_url, list_path) for submission_url in submission_urls
        ]

        # Check for duplicates within the submission itself.
        logging.info("Checking for duplicates within the submission")
        url2name = {}
        for sub in self.submissions:
            if url2name.get(sub.normalized_url, None) is not None:
                Utils.error_exit(
                    f"Duplicated submission found: {sub.name} - {sub.normalized_url}"
                )
            url2name[sub.normalized_url] = sub.name

        # Assemble the list of Library Manager indexer logs URLs for the submissions
        #   to show in the acceptance message.
        logging.info("Creating index entry")
        self.index_entry = "\n".join(sub.index_entry for sub in self.submissions)
        logging.info("SubmissionRequest index_entry:")
        logging.info(Utils.indent(self.index_entry))


def main() -> int:
    parser = argparse.ArgumentParser("pr_submission_parser")

    parser.add_argument(
        "--diffpath",
        required=True,
        help="Path to PR diff file.",
    )
    parser.add_argument(
        "--listpath",
        required=True,
        help="Path to List file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        default=None,
        help="Path to output file. Output is printed to STDOUT otherwise.",
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
    diff_loc = args.diffpath
    list_loc = args.listpath

    logging.basicConfig(level=VERBOSITY_LEVELS[args.verbosity])
    logging.debug(f"{args = }")

    diff_path = Path(diff_loc)
    list_path = Path(list_loc)
    logging.debug(f"{diff_path = }")
    logging.debug(f"{list_path = }")

    if not diff_path.exists():
        Utils.error_exit(f"diff file must exist: {diff_path}")

    if not list_path.exists():
        Utils.error_exit(f"list file must exist: {list_path}")

    req = SubmissionRequest(diff_path, list_path)

    logging.info("Converting SubmissionRequest to JSON")
    json_str = json.dumps(req, cls=MyEncoder, indent=OUTPUT_INDENTATION)
    logging.debug(f"{json_str = }")

    logging.info("Writing output")
    if args.output is None:
        print(json_str)

    else:
        with open(args.output, "a") as f:
            print(json_str, file=f)

    logging.info("All Done")
    return 0


if __name__ == "__main__":
    code = main()

    exit(code)
