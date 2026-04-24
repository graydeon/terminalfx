from __future__ import annotations

import cv2
import numpy as np

from terminalfx.config.schema import PreviewConfig
from terminalfx.core.types import Frame, PreviewMode
from terminalfx.media.frames import ascii_to_frame, frame_to_ascii


class PreviewRenderer:
    def __init__(self, preview: PreviewConfig) -> None:
        self.preview = preview

    def render(self, frame: Frame, mode: PreviewMode, hud: list[str] | None = None) -> Frame:
        if mode == PreviewMode.PIXEL:
            canvas = frame.copy()
        else:
            text = frame_to_ascii(
                frame,
                self.preview.character_width,
                self.preview.character_height,
                ramp=" .:-=+*#%@",
            )
            canvas = ascii_to_frame(text, frame.shape[1], frame.shape[0])
            canvas[::4, :, :] = np.maximum(canvas[::4, :, :], np.array([5, 16, 5], dtype=np.uint8))
        self._draw_hud(canvas, hud or [])
        return canvas

    def waiting_frame(self, width: int, height: int, lines: list[str]) -> Frame:
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self._draw_hud(canvas, ["terminalfx preview", *lines])
        return canvas

    def _draw_hud(self, frame: Frame, lines: list[str]) -> None:
        cv2.rectangle(
            frame, (18, 18), (frame.shape[1] - 18, frame.shape[0] - 18), (210, 255, 220), 1
        )
        y = 44
        for line in lines[:9]:
            cv2.putText(
                frame,
                line,
                (30, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (220, 255, 230),
                1,
                cv2.LINE_AA,
            )
            y += 24
        cv2.putText(
            frame,
            "ESC/q exit",
            (frame.shape[1] - 190, 44),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (220, 255, 230),
            1,
            cv2.LINE_AA,
        )
