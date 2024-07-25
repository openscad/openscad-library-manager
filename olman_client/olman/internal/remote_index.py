import json
from time import time

from olman import model, state, utils
from olman.files import platform

INDEX_FILE_NAME = "remote_index.json"
INDEX_FILE_LINK = f"https://raw.githubusercontent.com/openscad/openscad-library-manager/main/output_files/{INDEX_FILE_NAME}"


class RemoteIndex:
    def __init__(self, update=False, load=True):
        if update:
            self.update()

        if load:
            self._load()

    @property
    def index_file_path(self):
        return platform.getDataDir() / INDEX_FILE_NAME

    def _download(self):
        idx_path = self.index_file_path

        idx_path.parent.mkdir(parents=True, exist_ok=True)

        utils.downloadFile(
            url=INDEX_FILE_LINK,
            dst=idx_path,
        )

    def _load(self):
        idx_path = self.index_file_path

        if not idx_path.exists():
            self._download()

        with open(idx_path, "r") as f:
            data = json.load(f)

        libraries = [
            model.RemoteLibrary(**remote_lib) for remote_lib in data["libraries"]
        ]

        self._libraries = utils.bucket(
            libraries,
            key=lambda remote_lib: remote_lib.manifest.library.name,
        )

    def update(self, force: bool = False) -> bool:
        threshold = 4 * 3600  # 4 hours
        dt = state.lastUpdateTime()
        index_file_path = platform.getDataDir() / INDEX_FILE_NAME

        if force or dt >= threshold or not index_file_path.exists():
            self._download()

            state.State.set("last-update", int(time()))

            return True

        return False

    def get(self, name: str, version: str | None = None) -> list[model.RemoteLibrary]:
        # version= >=2.5
        # version= latest
        if version is None or version in ["*", "all"]:
            return self._libraries[name]

        if version in ["any", "latest"]:
            return self._libraries[name][-1:]

        # TODO: implement version comparison first
        # check if constrained or not
        if "0" <= version[0] <= "9":
            pass

        # process
        pass
