from __future__ import annotations

from pathlib import Path
from typing import cast

import cv2

from terminalfx.core.errors import SourceError
from terminalfx.core.types import Frame, FramePacket, SourceKind, TimePoint
from terminalfx.sources.base import SourceCapabilities, SourceInfo


class VideoFileSource:
    def __init__(self, path: Path, loop: bool = True) -> None:
        self.path = path
        self.loop = loop
        self._capture: cv2.VideoCapture | None = None
        self._info: SourceInfo | None = None
        self._frame_index = 0

    def open(self) -> SourceInfo:
        capture = cv2.VideoCapture(str(self.path))
        if not capture.isOpened():
            raise SourceError(f"unable to open video file: {self.path}")
        self._capture = capture
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frame_count / fps if fps and frame_count else None
        self._info = SourceInfo(
            kind=SourceKind.FILE,
            name=self.path.name,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration,
            capabilities=SourceCapabilities(seekable=True, live=False, has_audio=False),
        )
        self._frame_index = 0
        return self._info

    def read(self, time: TimePoint | None = None) -> FramePacket | None:
        if self._capture is None:
            raise SourceError("video source is not open")
        if time is not None:
            self.seek(time)
        ok, frame = self._capture.read()
        if not ok and self.loop:
            self.seek(TimePoint())
            ok, frame = self._capture.read()
        if not ok:
            return None
        info = self._require_info()
        frame_index = int(self._capture.get(cv2.CAP_PROP_POS_FRAMES) or self._frame_index)
        point = TimePoint(seconds=max(0, frame_index - 1) / info.fps, frame=max(0, frame_index - 1))
        self._frame_index = frame_index
        return FramePacket(frame=cast(Frame, frame), time=point, source_name=info.name)

    def seek(self, time: TimePoint) -> None:
        if self._capture is None:
            raise SourceError("video source is not open")
        frame_index = time.frame
        if frame_index <= 0 and time.seconds > 0:
            frame_index = int(time.seconds * self._require_info().fps)
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        self._frame_index = frame_index

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None

    def _require_info(self) -> SourceInfo:
        if self._info is None:
            raise SourceError("video source metadata is unavailable")
        return self._info
