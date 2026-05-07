"""Tests for normalize_frame edge cases, degenerate frames, and aspect ratios."""

import numpy as np

from terminalfx.media.frames import normalize_frame


def test_normalize_zero_width_returns_blank() -> None:
    frame = np.zeros((90, 0, 3), dtype=np.uint8)
    result = normalize_frame(frame, 160, 90)
    assert result.shape == (90, 160, 3)
    assert np.array_equal(result, np.zeros((90, 160, 3), dtype=np.uint8))


def test_normalize_zero_height_returns_blank() -> None:
    frame = np.zeros((0, 160, 3), dtype=np.uint8)
    result = normalize_frame(frame, 160, 90)
    assert result.shape == (90, 160, 3)
    assert np.array_equal(result, np.zeros((90, 160, 3), dtype=np.uint8))


def test_normalize_zero_both_returns_blank() -> None:
    frame = np.zeros((0, 0, 3), dtype=np.uint8)
    result = normalize_frame(frame, 160, 90)
    assert result.shape == (90, 160, 3)
    assert np.array_equal(result, np.zeros((90, 160, 3), dtype=np.uint8))


def test_normalize_empty_array_returns_blank() -> None:
    frame = np.array([], dtype=np.uint8).reshape(0, 0, 3)
    result = normalize_frame(frame, 160, 90)
    assert result.shape == (90, 160, 3)


def test_normalize_single_pixel() -> None:
    frame = np.full((1, 1, 3), 128, dtype=np.uint8)
    result = normalize_frame(frame, 160, 90)
    assert result.shape == (90, 160, 3)
    assert result.mean() > 0


def test_normalize_extreme_aspect_ratio() -> None:
    frame = np.full((10, 1000, 3), 200, dtype=np.uint8)
    result = normalize_frame(frame, 160, 90)
    assert result.shape == (90, 160, 3)
    assert result.mean() > 0


def test_normalize_preserves_aspect_by_cropping_to_fill() -> None:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    frame[:, :40] = (255, 0, 0)
    frame[:, 120:] = (0, 0, 255)

    normalized = normalize_frame(frame, 160, 90)

    assert normalized.shape == (90, 160, 3)
    assert normalized[:, :8].mean() > 0
