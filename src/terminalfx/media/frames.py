from __future__ import annotations

from typing import cast

import cv2
import numpy as np

from terminalfx.core.types import Frame


def normalize_frame(frame: Frame, width: int, height: int) -> Frame:
    source_h, source_w = frame.shape[:2]
    if source_w <= 0 or source_h <= 0:
        return cast(Frame, np.zeros((height, width, 3), dtype=np.uint8))

    # Fast-path: dimensions already match — avoid resize overhead
    if source_w == width and source_h == height:
        return frame

    scale = max(width / source_w, height / source_h)
    scaled_w = max(width, int(round(source_w * scale)))
    scaled_h = max(height, int(round(source_h * scale)))
    resized = cv2.resize(frame, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
    x0 = max(0, (scaled_w - width) // 2)
    y0 = max(0, (scaled_h - height) // 2)
    cropped = resized[y0 : y0 + height, x0 : x0 + width]
    return cast(Frame, cropped.copy())


def frame_to_ascii(
    frame: Frame, width: int, height: int, ramp: str, invert: bool = False
) -> str:
    """Convert a frame to ASCII art using OpenCV + numpy (PIL-free hot path)."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_AREA)

    active_ramp = ramp[::-1] if invert else ramp
    bins = np.linspace(0, 255, num=len(active_ramp), endpoint=True)
    indices = np.digitize(gray, bins, right=True).clip(0, len(active_ramp) - 1)

    # Vectorized: map indices to characters in one numpy operation
    char_array = np.array(list(active_ramp), dtype="U1")
    result_chars = char_array[indices]
    return "\n".join("".join(row) for row in result_chars)


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


# Pre-rendered glyph atlas for faster ASCII-to-frame conversion.
# Renders all ramp characters once at common cell sizes.
_glyph_atlas: dict[tuple[str, int, int], Frame] = {}


def ascii_to_frame_fast(
    ascii_frame: str,
    width: int,
    height: int,
    color: tuple[int, int, int] = (125, 255, 145),
) -> Frame:
    """Optimized ASCII-to-frame using pre-rendered glyph atlas.

    Avoids per-character cv2.getTextSize/cv2.putText in the hot path
    by pre-rendering glyphs into a shared atlas.
    """
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    lines = ascii_frame.splitlines()
    if not lines:
        return canvas
    rows = len(lines)
    cols = max(len(line) for line in lines)
    cell_w = max(1, width // cols)
    cell_h = max(1, height // rows)

    # Ensure atlas has glyphs for this cell size
    _ensure_atlas(cell_w, cell_h, color)

    for row, line in enumerate(lines):
        y_start = row * cell_h
        y_end = min(y_start + cell_h, height)
        for col, char in enumerate(line):
            if char == " ":
                continue
            x_start = col * cell_w
            x_end = min(x_start + cell_w, width)
            tile = _glyph_atlas.get((char, cell_w, cell_h))
            if tile is None:
                continue
            th = y_end - y_start
            tw = x_end - x_start
            if th > 0 and tw > 0:
                canvas[y_start:y_end, x_start:x_end] = np.maximum(
                    canvas[y_start:y_end, x_start:x_end], tile[:th, :tw]
                )
    return canvas


_ATLAS_COLOR: tuple[int, int, int] = (0, 0, 0)
_ATLAS_CELL: tuple[int, int] = (0, 0)


def _ensure_atlas(cell_w: int, cell_h: int, color: tuple[int, int, int]) -> None:
    global _ATLAS_COLOR, _ATLAS_CELL
    key = (cell_w, cell_h)
    if key == _ATLAS_CELL and color == _ATLAS_COLOR:
        return
    _ATLAS_CELL = key
    _ATLAS_COLOR = color
    ramp = " .:-=+*#%@"
    for ch in ramp:
        _glyph_atlas[(ch, cell_w, cell_h)] = _glyph_tile(ch, cell_w, cell_h, color)


def _glyph_tile(
    char: str, width: int, height: int, color: tuple[int, int, int]
) -> Frame:
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
