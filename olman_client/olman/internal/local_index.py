import fnmatch
import json
import shutil
from pathlib import Path
from time import time

from olman import model, state, utils
from olman.files import platform

INDEX_FILE_NAME = "local_index.json"


class LocalIndex:
    def __init__(self):
        self._load()

    @property
    def index_file_path(self):
        return platform.getDataDir() / INDEX_FILE_NAME

    def _initialize(self, exist_ok=False):
        idx_path = self.index_file_path

        if not exist_ok and idx_path.exists():
            raise FileExistsError("Local index already exists")

        idx_path.parent.mkdir(parents=True, exist_ok=True)
        with open(idx_path, "w") as f:
            json.dump({"libraries": []}, f)

    def _load(self):
        idx_path = self.index_file_path

        if not idx_path.exists():
            self._initialize()

        with open(idx_path, "r") as f:
            data = json.load(f)

        libraries = [model.LocalLibrary(**local_lib) for local_lib in data["libraries"]]

        self._libraries = utils.bucket(
            libraries,
            key=lambda local_lib: local_lib.manifest.library.name,
        )

        for k, v in self._libraries:
            if len(v) > 1:
                raise Exception("Local index is corrupted")

    def _dump(self):
        with open(self.index_file_path, "w") as f:
            json.dump(
                {
                    "libraries": [
                        local_libs[0].model_dump()
                        for local_libs in self._libraries.values()
                    ]
                },
                f,
            )

    def add(self, manifest: model.Manifest, location: Path):
        new_lib = model.LocalLibrary(
            manifest=manifest,
            location=location.as_posix(),
            date_added=time(),
        )

        if (name := new_lib.manifest.library.name) in self._libraries.keys():
            raise Exception(f"{name} already exists and can not be added again")

        self._libraries[name].append(new_lib)

        self._dump()

    def remove(self, name: str):
        self._libraries.pop(name, None)

        self._dump()

    def get(self, name: str) -> list[model.LocalLibrary]:
        matches = self._libraries[name]

        # if len(matches) != 1:
        #     raise Exception(f"No installed library named {name}")

        return matches
