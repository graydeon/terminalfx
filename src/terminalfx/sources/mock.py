from __future__ import annotations

import math

import cv2
import numpy as np

from terminalfx.core.types import Frame, FramePacket, Resolution, SourceKind, TimePoint
from terminalfx.sources.base import SourceCapabilities, SourceInfo


class MockSource:
    def __init__(self, resolution: Resolution, name: str = "mock") -> None:
        self.resolution = resolution
        self.name = name
        self.index = 0

    def open(self) -> SourceInfo:
        self.index = 0
        return SourceInfo(
            kind=SourceKind.MOCK,
            name=self.name,
            width=self.resolution.width,
            height=self.resolution.height,
            fps=float(self.resolution.fps),
            duration_seconds=None,
            capabilities=SourceCapabilities(seekable=True, live=False),
        )

    def read(self, time: TimePoint | None = None) -> FramePacket:
        point = time or TimePoint(seconds=self.index / self.resolution.fps, frame=self.index)
        frame = self._frame(point)
        self.index = point.frame + 1
        return FramePacket(frame=frame, time=point, source_name=self.name)

    def seek(self, time: TimePoint) -> None:
        self.index = time.frame

    def close(self) -> None:
        return None

    def _frame(self, time: TimePoint) -> Frame:
        height, width = self.resolution.height, self.resolution.width
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        phase = time.seconds
        x = np.linspace(0, 1, width, dtype=np.float32)
        y = np.linspace(0, 1, height, dtype=np.float32)[:, None]
        wave = (
            np.sin((x * 10.0 + phase * 2.4) * math.pi) + np.cos((y * 8.0 - phase) * math.pi)
        ) * 0.5
        frame[:, :, 1] = np.clip((wave + 1.0) * 95, 0, 255).astype(np.uint8)
        frame[:, :, 2] = np.clip(x * 120 + 40, 0, 255).astype(np.uint8)
        frame[:, :, 0] = np.clip(y * 140 + 20, 0, 255).astype(np.uint8)
        center = (int((0.5 + math.sin(phase) * 0.2) * width), int(height * 0.5))
        cv2.circle(frame, center, max(12, min(width, height) // 8), (220, 255, 230), 2)
        cv2.putText(
            frame,
            "terminalfx",
            (max(12, width // 20), max(32, height // 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            max(0.5, width / 900),
            (235, 255, 240),
            1,
            cv2.LINE_AA,
        )
        return frame
