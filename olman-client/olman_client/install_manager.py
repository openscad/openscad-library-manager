from shutil import rmtree

from olman_client import utils
from olman_client.files.platform import getDataDir
from olman_client.internal import local_index, remote_index

DOWNLOAD_LOCATION = getDataDir()
INSTALL_LOCATION = getDataDir()


def install(name: str, version_exact: str, *, force=False, reinstall=False):
    # remote_index.update()

    if local_lib := local_index.get(name, default=None):
        if utils.version_eq(local_lib.manifest.library.version, version_exact):
            if reinstall:
                remove(name)

            else:
                print(f"{name}:{version_exact} is already installed")
                return

        elif force:
            remove(name)

        else:
            raise Exception("Another version is already installed")

    remote_lib = remote_index.get(
        name, version_exact, default=None
    )  # TODO: change 'get' to search?

    if remote_lib is None:
        raise Exception(f"Could not find {name}:{version_exact} in the index")

    compressed_lib_path = utils.downloadFile(
        remote_lib.download_link, dst=DOWNLOAD_LOCATION
    )
    lib_path = utils.extractFile(compressed_lib_path, dst_dir=INSTALL_LOCATION)
    lib_path = lib_path.rename(lib_path.with_name(name))
    compressed_lib_path.unlink()
    local_index.add(remote_lib.manifest, lib_path)


def remove(name: str, missing_ok: bool = True):
    if local_lib := local_index.get(name, default=None):
        rmtree(local_lib.location)
        local_index.remove(name)

    elif not missing_ok:
        raise Exception(f"Library {name} not found.")
