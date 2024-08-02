import tarfile
import zipfile
from collections import defaultdict
from pathlib import Path
from shutil import rmtree
from typing import Callable, Hashable, Iterable


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

    else:
        dst_dir = dst_dir / file.stem

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


def bucket[
    T1, T2: Hashable
](iterable: Iterable[T1], key: Callable[[T1], T2]) -> defaultdict[T2, list[T1]]:
    result: defaultdict[T2, list[T1]] = defaultdict(list)

    for item in iterable:
        result[key(item)].append(item)

    return result
