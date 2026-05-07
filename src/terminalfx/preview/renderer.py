from __future__ import annotations

import cv2
import numpy as np

from terminalfx.config.schema import PreviewConfig
from terminalfx.core.types import Frame, PreviewMode
from terminalfx.media.frames import ascii_to_frame_fast, frame_to_ascii


class PreviewRenderer:
    def __init__(self, preview: PreviewConfig) -> None:
        self.preview = preview
        self._scanline_mask: Frame | None = None
        self._last_width: int = 0
        self._last_height: int = 0

    def render(
        self,
        frame: Frame,
        mode: PreviewMode,
        hud: list[str] | None = None,
        *,
        source_is_live: bool = False,
    ) -> Frame:
        # AUTO: pixel for live sources (fast), ascii for offline (pretty)
        effective_mode = mode
        if mode == PreviewMode.AUTO:
            effective_mode = PreviewMode.PIXEL if source_is_live else PreviewMode.ASCII

        if effective_mode == PreviewMode.PIXEL:
            canvas = frame
        else:
            text = frame_to_ascii(
                frame,
                self.preview.character_width,
                self.preview.character_height,
                ramp=" .:-=+*#%@",
            )
            canvas = ascii_to_frame_fast(text, frame.shape[1], frame.shape[0])
            # Scanline overlay — precomputed mask when dimensions stable
            h, w = frame.shape[:2]
            if h != self._last_height or w != self._last_width:
                mask = np.zeros((h, w, 3), dtype=np.uint8)
                mask[::4, :, :] = np.array([5, 16, 5], dtype=np.uint8)
                self._scanline_mask = mask
                self._last_height = h
                self._last_width = w
            canvas = np.maximum(canvas, self._scanline_mask)  # type: ignore[arg-type]

        self._draw_hud(canvas, hud or [])
        return canvas

    def waiting_frame(
        self, width: int, height: int, lines: list[str]
    ) -> Frame:
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        self._draw_hud(canvas, ["terminalfx preview", *lines])
        return canvas

    def _draw_hud(self, frame: Frame, lines: list[str]) -> None:
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (18, 18), (w - 18, h - 18), (210, 255, 220), 1)
        y = 44
        for line in lines[:9]:
            cv2.putText(
                frame, line, (30, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (220, 255, 230), 1, cv2.LINE_AA,
            )
            y += 24
        cv2.putText(
            frame, "ESC/q exit", (w - 190, 44),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (220, 255, 230), 1, cv2.LINE_AA,
        )
