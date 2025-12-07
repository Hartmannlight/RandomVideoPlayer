from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

from randomvideoplayer.file_logger import FileLogger


def iter_webm_files(directory: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            for name in files:
                if name.lower().endswith('.webm'):
                    yield root_path / name
    else:
        with os.scandir(directory) as it:
            for entry in it:
                if entry.is_file() and entry.name.lower().endswith('.webm'):
                    yield directory / entry.name


def write_playlist_file(
    files: Iterable[Path],
    playlist_path: Path,
    logger: Optional[FileLogger] = None,
) -> int:
    if logger is not None:
        logger.log(f'Building playlist at {playlist_path}')
    playlist_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with playlist_path.open('w', encoding='utf-8') as f:
        for path in files:
            f.write(path.resolve().as_posix() + '\n')
            count += 1
    if logger is not None:
        logger.log(f'Playlist written to {playlist_path} with {count} entries')
    return count
