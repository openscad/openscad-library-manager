from pathlib import Path

TEST_DIR = Path(__file__).parent / "output_dir"
# TEST_DIR.mkdir(parents=True, exist_ok=True)
OLMAN_FOLDER_NAME = "olman"


def getXdgConfigDir() -> Path:
    """
    `$XDG_CONFIG_HOME` defines the base directory relative to which user-specific
    configuration files should be stored.

    see: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    return TEST_DIR / "config"  # TODO: Remove
    return Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()


def getXdgDataDir() -> Path:
    """
    `$XDG_DATA_HOME` defines the base directory relative to which user-specific data files
    should be stored.

    see: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    return TEST_DIR / "data"  # TODO: Remove
    return Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()


def getXdgStateDir() -> Path:
    """
    `$XDG_STATE_HOME` defines the base directory relative to which user-specific state files
    should be stored. Contains state data that should persist between (application) restarts,
    but that is not important or portable enough to the user that it should be stored in
    `$XDG_DATA_HOME`.

    see: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    return TEST_DIR / "state"  # TODO: Remove
    return Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()


def getXdgCacheDir() -> Path:
    """
    `$XDG_CACHE_HOME` defines the base directory relative to which user-specific non-essential data files should be stored.

    see: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
    """
    return TEST_DIR / "cache"  # TODO: Remove
    return Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()


def getDataDir() -> Path:
    data_dir = getXdgDataDir() / OLMAN_FOLDER_NAME

    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def getCacheDir() -> Path:
    cache_dir = getXdgCacheDir() / OLMAN_FOLDER_NAME

    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)

    return cache_dir
