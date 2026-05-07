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
        # Precompute static patterns once
        h, w = resolution.height, resolution.width
        self._x_grad = np.clip(
            np.linspace(0, 1, w, dtype=np.float32) * 120 + 40, 0, 255
        ).astype(np.uint8)
        self._y_grad = np.clip(
            np.linspace(0, 1, h, dtype=np.float32)[:, None] * 140 + 20, 0, 255
        ).astype(np.uint8)
        self._x_wave = np.linspace(0, 1, w, dtype=np.float32)
        self._y_wave = np.linspace(0, 1, h, dtype=np.float32)[:, None]

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
        point = time or TimePoint(
            seconds=self.index / self.resolution.fps, frame=self.index
        )
        frame = self._frame(point)
        self.index = point.frame + 1
        return FramePacket(frame=frame, time=point, source_name=self.name)

    def seek(self, time: TimePoint) -> None:
        self.index = time.frame

    def close(self) -> None:
        return None

    def _frame(self, time: TimePoint) -> Frame:
        h, w = self.resolution.height, self.resolution.width
        phase = time.seconds

        # Build frame from precomputed gradients + cheap wave
        wave = (
            np.sin(self._x_wave * 10.0 + phase * 2.4)
            + np.cos(self._y_wave * 8.0 - phase)
        ) * 0.5
        green = np.clip((wave + 1.0) * 95, 0, 255).astype(np.uint8)

        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:, :, 0] = self._y_grad
        frame[:, :, 1] = green
        frame[:, :, 2] = self._x_grad

        center = (
            int((0.5 + math.sin(phase) * 0.2) * w),
            int(h * 0.5),
        )
        cv2.circle(frame, center, max(12, min(w, h) // 8), (220, 255, 230), 2)
        cv2.putText(
            frame,
            "terminalfx",
            (max(12, w // 20), max(32, h // 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            max(0.5, w / 900),
            (235, 255, 240),
            1,
            cv2.LINE_AA,
        )
        return frame
