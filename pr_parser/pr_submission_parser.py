import argparse
import json
import os
import subprocess
import tempfile
import tomllib
from enum import StrEnum
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import requests
import unidiff

MANIFEST_FILENAME = "manifest.toml"
INDEX_SOURCE_SEPARATOR = "||"
OUTPUT_INDENTATION = 2

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
        print(f"ERROR: {msg}")
        exit(0)

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
        # normalize and validate URL
        url_obj = urlparse(submission_url)

        # check if URL is accessible
        if not Utils.url_accessible(url_obj):
            Utils.error_exit("Unable to load submission URL. Is the repository public?")

        # normalize url
        normalized_url = Utils.normalize_git_url(url_obj)

        # Check if url is from a supported Git host
        if not Utils.url_is_under(normalized_url, SUPPORTED_HOSTS):
            Utils.error_exit(
                f"{normalized_url.hostname} is not currently supported as a Git hosting website."
            )

        # Check if URL is a Git repository
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

        with open(list_path, "r") as list_file:
            for list_line in list_file.readline():
                normalized_list_url = Utils.normalize_git_url(list_line)

                if normalized_url == normalized_list_url:
                    Utils.error_exit("URL is already in the list")

        self.official = Utils.url_is_under(normalized_url, OFFICIAL_ORGANIZATIONS)

        self._parse_submission_repo()

    def _parse_submission_repo(self):
        with tempfile.TemporaryDirectory() as submission_repo_directory:
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
            subprocess.run(
                ["git", "fetch", "--tags"],
                cwd=submission_repo_directory,
                capture_output=True,
                check=True,
            )

            proc = subprocess.run(
                ["git", "rev-list", "--tags", "--max-count=1"],
                cwd=submission_repo_directory,
                capture_output=True,
                text=True,
                check=True,
            )
            tag_sha = proc.stdout.strip()

            if tag_sha == "":
                Utils.error_exit("The repository has no tags.")

            proc = subprocess.run(
                ["git", "describe", "--tags", tag_sha],
                cwd=submission_repo_directory,
                capture_output=True,
                text=True,
                check=True,
            )

            self.tag = proc.stdout.strip()

            # Checkout latest tag
            subprocess.run(
                ["git", "checkout", self.tag],
                cwd=submission_repo_directory,
                capture_output=True,
                check=True,
            )

            # Get submission library name.
            # It is necessary to record this in the index source entry because
            #   the library is locked to this name.
            manifest_path = Path(submission_repo_directory) / MANIFEST_FILENAME
            with open(manifest_path, "rb") as f:
                manifest_data = tomllib.load(f, parse_float=lambda x: x)

            # # TODO: parse manifest here
            # manifest_data: dict

            self.name = manifest_data["library"]["name"]
            self.index_entry = INDEX_SOURCE_SEPARATOR.join(
                (self.normalized_url, self.name)
            )


class SubmissionRequest:  # pull request
    # type: str
    # submissions: list[Submission]
    # index_entry: str
    def __init__(self, diff_path: Path, list_path: Path) -> None:
        # Read PR diff
        with open(diff_path, encoding="utf-8") as diff_file:
            raw_diff_data = diff_file.read()

        # Check if the PR has removed the final newline from a file, which would
        #   cause a spurious diff for the next PR if merged.
        if raw_diff_data.endswith("\\ No newline at end of file\n"):
            Utils.error_exit(
                f"Pull request removes newline from the end of a file.\n"
                "Please add a blank line to the end of the file."
            )

        diffs = unidiff.PatchSet(raw_diff_data)

        if (
            (len(diffs) != 1)
            or (Path(diffs[0].source_file).name != list_path.name)
            or (Path(diffs[0].target_file).name != list_path.name)
        ):
            Utils.error_exit(f"Not a library manager submission.")

        additions = 0
        deletions = 0
        submission_urls = []

        for hunk in diffs[0]:
            for raw_diff_line in str(hunk).splitlines():
                diff_line = raw_diff_line.lstrip()
                if diff_line.startswith("+"):
                    additions += 1
                    submission_urls.append(diff_line[1:])

                elif diff_line.startswith("-"):
                    deletions += 1

                else:
                    continue

        if additions == 0 and deletions == 0:
            self.type = "other"

        elif additions > 0 and deletions == 0:
            self.type = "addition"

        elif additions == 0 and deletions > 0:
            self.type = "removal"

        else:
            self.type = "modification"

        # Parse submission urls
        self.submissions = [
            Submission(submission_url, list_path) for submission_url in submission_urls
        ]

        # Check for duplicates within the submission itself.
        url2name = {}
        for sub in self.submissions:
            if url2name.get(sub.normalized_url, None) is not None:
                Utils.error_exit(
                    f"Duplicated submission found: {sub.name} - {sub.normalized_url}"
                )
            url2name[sub.normalized_url] = sub.name

        # Assemble the list of Library Manager indexer logs URLs for the submissions
        #   to show in the acceptance message.
        self.index_entry = "\n".join(sub.index_entry for sub in self.submissions)


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

    args = parser.parse_args()
    diff_loc = args.diffpath
    list_loc = args.listpath

    diff_path = Path(diff_loc)
    list_path = Path(list_loc)

    if not diff_path.exists():
        Utils.error_exit(f"diff file must exist: {diff_path}")

    if not list_path.exists():
        Utils.error_exit(f"list file must exist: {list_path}")

    req = SubmissionRequest(diff_path, list_path)

    json_str = json.dumps(req, cls=MyEncoder, indent=OUTPUT_INDENTATION)
    print(json_str)

    return 0


if __name__ == "__main__":
    code = main()

    exit(code)
