import tarfile
import zipfile
from collections import defaultdict
from pathlib import Path
from shutil import rmtree
from typing import Callable, Hashable, Iterable
from urllib.request import urlretrieve

from libversion import version_compare2

_VERSION_EQUAL = 0
_VERSION_LESS = -1
_VERSION_GREATER = 1


def getFileDownloadLink(repo_url: str, file_path: str, branch: str = "main"):
    # Remove any leading or trailing slashes from the arguments
    repo_url = repo_url.strip("/")
    branch = branch.strip("/")
    file_path = file_path.strip("/")

    repo_parts = repo_url.split("/")
    if "github.com" in repo_parts:
        # Extract the username and repository name from the repo link
        username = repo_parts[-2]
        repo_name = repo_parts[-1]

        # Construct the raw file URL
        download_link = f"https://raw.githubusercontent.com/{username}/{repo_name}/{branch}/{file_path}"

    return download_link


def getRepoZipLink(repo_link, branch="main", tag=None, sha=None):
    """
    Generate a GitHub repository download link as a zip file.

    Parameters:
        repo_link (str): URL of the GitHub repository.
        branch (str, optional): Branch name. Default is "main".
        tag (str, optional): Tag name. If provided, the link will point to the tag.
        sha (str, optional): Full SHA hash. If provided, the link will point to the specific commit.

    Returns:
        str: URL to the zip file of the repository.
    """
    # Remove any leading or trailing slashes from the arguments
    repo_link = repo_link.strip("/")
    branch = branch.strip("/")
    tag = tag.strip("/") if tag is not None else None
    sha = sha.strip("/") if sha is not None else None

    repo_parts = repo_link.split("/")

    # Extract the username and repository name from the repo link
    if "github.com" in repo_parts:
        username = repo_parts[-2]
        repo_name = repo_parts[-1].strip(".git")

        # Construct the zip file URL
        if tag:
            zip_link = (
                f"https://github.com/{username}/{repo_name}/archive/refs/tags/{tag}.zip"
            )

        elif sha:
            zip_link = f"https://github.com/{username}/{repo_name}/archive/{sha}.zip"

        elif branch:
            zip_link = f"https://github.com/{username}/{repo_name}/archive/refs/heads/{branch}.zip"

        else:
            raise ValueError("Unexpected arugments.")

    return zip_link


def downloadFile(url: str, dst: str | Path, exist_ok: bool = False) -> Path:
    dst = Path(dst)

    tmp_path, response = urlretrieve(url=url)
    tmp_path = Path(tmp_path)

    if dst.is_dir():
        file_name = response["content-disposition"].split("filename=")[1]

        dst = dst / file_name

        if dst.is_dir():
            raise FileExistsError(
                f"A directory with the same name exists: {dst / file_name}"
            )

    if not exist_ok and dst.is_file():
        raise FileExistsError(f"File already exists: {dst}")

    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst = tmp_path.rename(dst)

    return dst


def extractZipFile(file: Path, dst_dir: Path) -> Path:
    with zipfile.ZipFile(file, mode="r") as f:
        dirs = list({name.split("/")[0] for name in f.namelist() if "/" in name})

        if len(dirs) != 1:
            dst_dir = dst_dir / file.stem

        dst_dir.mkdir(parents=True, exist_ok=True)

        f.extractall(dst_dir)

        if len(dirs) == 1 and dirs[0] != file.stem:
            new_name = dst_dir / file.stem

            if new_name.exists():
                rmtree(new_name)

            (dst_dir / dirs[0]).rename(new_name)
            dst_dir = new_name

    return dst_dir


def extractTarFile(file: Path, dst_dir: Path) -> Path:
    with tarfile.open(file, "r") as f:
        f.extractall(dst_dir)

    return dst_dir


def extractFile(file: Path, dst_dir: Path) -> Path:
    if file.suffix.lower() == ".zip":
        return extractZipFile(file, dst_dir)

    elif file.suffix.lower() in [".tar", ".gz", ".bz2"]:
        return extractTarFile(file, dst_dir)

    else:
        raise ValueError("Unsupported file format")


def version_eq(v1: str, v2: str) -> bool:
    return version_compare2(v1, v2) == _VERSION_EQUAL


def version_lt(v1: str, v2: str) -> bool:
    return version_compare2(v1, v2) == _VERSION_LESS


def version_gt(v1: str, v2: str) -> bool:
    return version_compare2(v1, v2) == _VERSION_GREATER


def version_le(v1: str, v2: str) -> bool:
    return version_lt(v1, v2) or version_eq(v1, v2)


def version_ge(v1: str, v2: str) -> bool:
    return version_gt(v1, v2) or version_eq(v1, v2)


def bucket[
    T1, T2: Hashable
](iterable: Iterable[T1], key: Callable[[T1], T2]) -> defaultdict[T2, list[T1]]:
    result = defaultdict(list)

    for item in iterable:
        result[key(item)].append(item)

    return result


class _sentinel:
    pass
