from __future__ import annotations

from typing import cast

import cv2

from terminalfx.core.errors import SourceError
from terminalfx.core.types import Frame, FramePacket, SourceKind, TimePoint
from terminalfx.sources.base import SourceCapabilities, SourceInfo


class CameraSource:
    def __init__(
        self,
        camera_index: int = 0,
        target_width: int | None = None,
        target_height: int | None = None,
        target_fps: int | None = None,
    ) -> None:
        self.camera_index = camera_index
        self.target_width = target_width
        self.target_height = target_height
        self.target_fps = target_fps
        self._capture: cv2.VideoCapture | None = None
        self._info: SourceInfo | None = None
        self._frame_index = 0

    def open(self) -> SourceInfo:
        capture = cv2.VideoCapture(self.camera_index)
        if not capture.isOpened():
            raise SourceError(f"unable to open camera: {self.camera_index}")
        if self.target_width is not None:
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
        if self.target_height is not None:
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
        if self.target_fps is not None:
            capture.set(cv2.CAP_PROP_FPS, self.target_fps)
        self._capture = capture
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        self._info = SourceInfo(
            kind=SourceKind.CAMERA,
            name=f"camera:{self.camera_index}",
            width=int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0),
            height=int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0),
            fps=fps,
            capabilities=SourceCapabilities(seekable=False, live=True, has_audio=False),
        )
        return self._info

    def read(self, time: TimePoint | None = None) -> FramePacket | None:
        if self._capture is None or self._info is None:
            raise SourceError("camera source is not open")
        ok, frame = self._capture.read()
        if not ok:
            return None
        point = TimePoint(seconds=self._frame_index / self._info.fps, frame=self._frame_index)
        self._frame_index += 1
        return FramePacket(frame=cast(Frame, frame), time=point, source_name=self._info.name)

    def seek(self, time: TimePoint) -> None:
        raise SourceError("camera sources are not seekable")

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None
