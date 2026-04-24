from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import cv2

from terminalfx.core.errors import RenderError
from terminalfx.core.types import Frame


def write_png(frame: Frame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame):
        raise RenderError(f"unable to write PNG: {path}")
    return path


class Mp4Encoder:
    def __init__(self, path: Path, width: int, height: int, fps: int, codec: str = "mp4v") -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fourcc_factory = cast(Any, cv2).VideoWriter_fourcc
        fourcc = fourcc_factory(*codec)
        self._writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
        if not self._writer.isOpened():
            raise RenderError(f"unable to open MP4 writer: {path}")

    def write(self, frame: Frame) -> None:
        self._writer.write(frame)

    def close(self) -> None:
        self._writer.release()

    def __enter__(self) -> Mp4Encoder:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
