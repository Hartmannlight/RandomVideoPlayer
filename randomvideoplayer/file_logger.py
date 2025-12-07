from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Optional


class FileLogger:
    def __init__(self, enabled: bool, path: Optional[Path]) -> None:
        self.enabled = enabled and path is not None
        self.path = path
        self.lock = Lock()
        self.file = None
        if self.enabled and self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.file = self.path.open('a', encoding='utf-8', buffering=1)

    def log(self, message: str) -> None:
        if not self.enabled or self.file is None:
            return
        timestamp = datetime.now().isoformat(timespec='seconds')
        line = f'{timestamp}\t{message}\n'
        with self.lock:
            self.file.write(line)

    def close(self) -> None:
        if self.file is not None:
            with self.lock:
                self.file.close()
            self.file = None
