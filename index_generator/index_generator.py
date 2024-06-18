import json
import tempfile
import tomllib
from pathlib import Path
from subprocess import run

ACCEPTED_REPOSITORIES_FILENAME = "accepted_repositories.txt"
INDEX_FILENAME = "index_file.json"
MANIFEST_FILENAME = "manifest.toml"
INDEX_SOURCE_SEPARATOR = "||"
VALID_REPO_TYPES = [
    "OpenSCAD",
    "Partner",
    "Contributed",
    "test",
]


def error_exit(msg: str):
    print(f"ERROR: {msg}")
    exit(1)


def parse_repo(repo_url: str, lib_type: str, lib_name: str) -> list:
    with tempfile.TemporaryDirectory() as repo_directory:
        run(
            ["git", "clone", "--depth", "1", repo_url, repo_directory],
            cwd=repo_directory,
            capture_output=True,
            check=True,
        )

        # Get all tags in library repo
        run(
            ["git", "fetch", "--tags"],
            cwd=repo_directory,
            capture_output=True,
            check=True,
        )

        proc = run(
            ["git", "show-ref", "--tags"],
            cwd=repo_directory,
            capture_output=True,
            text=True,
            check=True,
        )

        tag_shas = [
            commit_tag.split()[0] for commit_tag in proc.stdout.strip().split("\n")
        ]

        # Parse manifest of every tag
        entries = []
        for tag_sha in tag_shas:
            run(
                ["git", "checkout", tag_sha],
                cwd=repo_directory,
                capture_output=True,
                check=True,
            )

            # Get library info from manifest
            manifest_path = Path(repo_directory) / MANIFEST_FILENAME
            with open(manifest_path, "rb") as f:
                manifest_data = tomllib.load(f)

            # Check name
            if manifest_data["library"]["name"] != lib_name:
                error_exit("mismatch")

            # Validate all fields

            # Add to list
            record = json.dumps(manifest_data["library"]) + ",\n"
            entries.append(record)

    return entries


def main():
    accepted_repositories_path = Path(__file__).parent / ACCEPTED_REPOSITORIES_FILENAME
    index_file_path = Path(__file__).parent / INDEX_FILENAME

    with open(index_file_path, "w") as f_index:
        f_index.write('{"libraries":[\n')

    with open(accepted_repositories_path, "r") as f_arp:
        while line := f_arp.readline():
            line = line.strip()

            if line.startswith("#"):
                continue

            repo_url, lib_type, lib_name = line.split(INDEX_SOURCE_SEPARATOR)

            # validate line
            if lib_type not in VALID_REPO_TYPES:
                error_exit(f"Invalid lib_type")

            # parse repo
            entries = parse_repo(repo_url, lib_type, lib_name)

            with open(index_file_path, "a") as f_index:
                f_index.writelines(entries)

    with open(index_file_path, "a") as f_index:
        f_index.write('"done"]}\n')


if __name__ == "__main__":
    main()
