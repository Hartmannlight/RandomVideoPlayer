from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import platform


def _get_config_path() -> Path:
    system = platform.system()
    if system == 'Windows':
        appdata = os.getenv('APPDATA')
        base_dir = Path(appdata) if appdata else Path.home()
        base_dir = base_dir / 'WebmPlayer'
    else:
        base_dir = Path.home() / 'WebmPlayer'
    return base_dir / 'config.json'


CONFIG_PATH = _get_config_path()


@dataclass
class AppConfig:
    directory: str = ''
    recursive: bool = False
    fullscreen: bool = True
    loop_playlist: bool = True
    shuffle: bool = True
    playlist_path: str = str(Path.home() / 'webm_playlist.m3u')
    mpv_path: str = ''
    logging_enabled: bool = False
    logging_path: str = str(Path.home() / 'randomvideoplayer.log')
    playback_log_enabled: bool = False
    playback_log_path: str = str(
        Path.home() / 'randomvideoplayer_playback.log',
    )


def load_config() -> AppConfig:
    if CONFIG_PATH.is_file():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            return AppConfig(**data)
        except Exception:
            return AppConfig()
    return AppConfig()


def save_config(config: AppConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(asdict(config), indent=2),
        encoding='utf-8',
    )
