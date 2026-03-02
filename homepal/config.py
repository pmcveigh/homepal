from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DATA_DIR = Path.home() / ".local" / "share" / "homepal"
CONFIG_DIR = Path.home() / ".config" / "homepal"
LOG_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "homepal.db"
CONFIG_PATH = CONFIG_DIR / "config.toml"


@dataclass(slots=True)
class AppPaths:
    data_dir: Path = DATA_DIR
    config_dir: Path = CONFIG_DIR
    db_path: Path = DB_PATH
    config_path: Path = CONFIG_PATH
    log_dir: Path = LOG_DIR



def ensure_directories(paths: AppPaths | None = None) -> AppPaths:
    paths = paths or AppPaths()
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(parents=True, exist_ok=True)
    return paths
