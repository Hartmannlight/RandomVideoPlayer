from __future__ import annotations

from pathlib import Path
from typing import Optional
import shutil


def find_mpv_executable(explicit_path: Optional[str]) -> str:
    if explicit_path:
        p = Path(explicit_path).expanduser()
        if p.is_file():
            return str(p)
        raise FileNotFoundError(f'mpv executable not found at "{p}"')

    candidates = ['mpv', 'mpv.exe']
    for candidate in candidates:
        found = shutil.which(candidate)
        if found is not None:
            return found

    raise FileNotFoundError(
        'mpv executable not found. Put mpv in PATH or set an explicit path.',
    )


def build_mpv_command(
    mpv_executable: str,
    playlist_path: Path,
    fullscreen: bool,
    loop_playlist: bool,
    shuffle: bool,
) -> list[str]:
    cmd: list[str] = [mpv_executable]

    cmd.append(f'--playlist={playlist_path.resolve().as_posix()}')

    if shuffle:
        cmd.append('--shuffle')
    if loop_playlist:
        cmd.append('--loop-playlist=inf')

    cmd.append('--prefetch-playlist=yes')
    cmd.append('--cache=yes')
    cmd.append('--cache-secs=10')
    cmd.append('--demuxer-readahead-secs=10')

    if fullscreen:
        cmd.append('--fs')

    return cmd
