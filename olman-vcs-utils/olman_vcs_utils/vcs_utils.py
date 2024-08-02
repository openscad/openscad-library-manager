from pathlib import Path
from urllib.request import urlretrieve


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


def getRepoZipLink(
    repo_link: str, branch: str = "main", tag: str | None = None, sha: str | None = None
):
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
        repo_name = repo_parts[-1]
        repo_name = repo_name[:-4] if repo_name.endswith(".git") else repo_name

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
