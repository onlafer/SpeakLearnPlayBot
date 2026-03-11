"""Локальное хранилище файлов (бесплатно, без облаков)."""

from pathlib import Path
from typing import Union

from common.config import CONFIG


def get_root() -> Path:
    """Корневая папка хранилища."""
    root = Path(CONFIG.storage.root)
    if not root.is_absolute():
        root = Path.cwd() / root
    return root


def get_full_path(relative_path: str) -> Path:
    """Полный путь к файлу по пути внутри хранилища (напр. videos/intro.mp4)."""
    return get_root() / relative_path


def ensure_dir(path: Path) -> None:
    """Создать родительские папки, если их нет."""
    path.parent.mkdir(parents=True, exist_ok=True)


def save_file(relative_path: str, source: Union[Path, bytes]) -> Path:
    """
    Сохранить файл в хранилище.
    source: путь к исходному файлу или байты содержимого.
    Возвращает полный путь к сохранённому файлу.
    """
    full_path = get_full_path(relative_path)
    ensure_dir(full_path)
    if isinstance(source, bytes):
        full_path.write_bytes(source)
    else:
        full_path.write_bytes(Path(source).read_bytes())
    return full_path


def exists(relative_path: str) -> bool:
    """Есть ли файл в хранилище."""
    return get_full_path(relative_path).is_file()
