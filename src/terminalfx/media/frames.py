from __future__ import annotations

from typing import cast

import cv2
import numpy as np
from PIL import Image

from terminalfx.core.types import Frame


def normalize_frame(frame: Frame, width: int, height: int) -> Frame:
    source_h, source_w = frame.shape[:2]
    if source_w <= 0 or source_h <= 0:
        return cast(Frame, cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA))

    scale = max(width / source_w, height / source_h)
    scaled_w = max(width, int(round(source_w * scale)))
    scaled_h = max(height, int(round(source_h * scale)))
    resized = cv2.resize(frame, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
    x0 = max(0, (scaled_w - width) // 2)
    y0 = max(0, (scaled_h - height) // 2)
    cropped = resized[y0 : y0 + height, x0 : x0 + width]
    return cast(Frame, cropped.copy())


def frame_to_ascii(frame: Frame, width: int, height: int, ramp: str, invert: bool = False) -> str:
    image = Image.fromarray(frame[:, :, ::-1])
    image = image.resize((width, height))
    gray = np.asarray(image.convert("L"), dtype=np.uint8)
    active_ramp = ramp[::-1] if invert else ramp
    bins = np.linspace(0, 255, num=len(active_ramp), endpoint=True)
    indices = np.digitize(gray, bins, right=True).clip(0, len(active_ramp) - 1)
    return "\n".join("".join(active_ramp[index] for index in row) for row in indices)


def ascii_to_frame(
    ascii_frame: str,
    width: int,
    height: int,
    color: tuple[int, int, int] = (125, 255, 145),
) -> Frame:
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    lines = ascii_frame.splitlines()
    if not lines:
        return canvas
    rows = len(lines)
    cols = max(len(line) for line in lines)
    x_edges = np.linspace(0, width, cols + 1, dtype=np.int32)
    y_edges = np.linspace(0, height, rows + 1, dtype=np.int32)
    glyphs: dict[tuple[str, int, int], Frame] = {}
    for row, line in enumerate(lines):
        y1 = int(y_edges[row])
        y2 = int(y_edges[row + 1])
        for col, char in enumerate(line.ljust(cols)):
            if char == " ":
                continue
            x1 = int(x_edges[col])
            x2 = int(x_edges[col + 1])
            cell_w = x2 - x1
            cell_h = y2 - y1
            key = (char, cell_w, cell_h)
            tile = glyphs.get(key)
            if tile is None:
                tile = _glyph_tile(char, cell_w, cell_h, color)
                glyphs[key] = tile
            canvas[y1:y2, x1:x2] = np.maximum(canvas[y1:y2, x1:x2], tile)
    return canvas


def _glyph_tile(char: str, width: int, height: int, color: tuple[int, int, int]) -> Frame:
    tile = np.zeros((height, width, 3), dtype=np.uint8)
    if width <= 0 or height <= 0:
        return tile
    font = cv2.FONT_HERSHEY_PLAIN
    base_size, base_line = cv2.getTextSize(char, font, 1.0, 1)
    base_width = max(1, base_size[0])
    base_height = max(1, base_size[1] + base_line)
    scale = min(width / base_width, height / base_height) * 0.92
    scale = max(0.1, scale)
    text_size, baseline = cv2.getTextSize(char, font, scale, 1)
    x = max(0, (width - text_size[0]) // 2)
    y = max(text_size[1], (height + text_size[1] - baseline) // 2)
    cv2.putText(tile, char, (x, y), font, scale, color, 1, cv2.LINE_AA)
    return tile
