from olman import utils
from olman.files.platform import getDataDir
from olman.internal import local_index, remote_index

DOWNLOAD_LOCATION = getDataDir()
INSTALL_LOCATION = getDataDir()


def install(name: str, version_exact: str, force=False):
    ridx = remote_index.RemoteIndex()
    lidx = local_index.LocalIndex()

    if local_matches := lidx.get(name):
        for local_lib in local_matches:
            if local_lib.manifest.library.version == version_exact:
                # TODO: log "already installed"
                return

            elif not force:
                raise Exception("Another version is already installed")

    remote_matches = ridx.get(name, version_exact)
    if len(remote_matches) != 1:
        raise Exception(f"Could not find {name}:{version_exact} in the index")

    remote_lib = remote_matches[0]
    compressed_lib_path = utils.downloadFile(
        remote_lib.download_link, dst=DOWNLOAD_LOCATION
    )
    lib_path = utils.extractFile(compressed_lib_path, dst_dir=INSTALL_LOCATION)
    lib_path = lib_path.rename(lib_path.with_name(name))
    compressed_lib_path.unlink()
    lidx.add(remote_lib.manifest, lib_path)


def remove(name: str):
    pass


install("test_lib_1", "1.0.0")
