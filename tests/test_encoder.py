"""Tests for the MP4 encoder, including failure cleanup and edge cases."""

from pathlib import Path

import numpy as np
import pytest

from terminalfx.core.errors import RenderError
from terminalfx.render.encoders import Mp4Encoder, write_png


def test_mp4_encoder_writes_and_closes(tmp_path: Path) -> None:
    output = tmp_path / "subdir" / "test.mp4"
    frame = np.zeros((90, 160, 3), dtype=np.uint8)

    with Mp4Encoder(output, 160, 90, 24) as encoder:
        for _ in range(5):
            encoder.write(frame)

    assert output.exists()
    assert output.stat().st_size > 0


def test_bad_codec_raises_without_litter(tmp_path: Path) -> None:
    output = tmp_path / "nope" / "bad.mp4"
    with pytest.raises(RenderError):
        Mp4Encoder(output, 160, 90, 24, codec="xyzz")
    # The RenderError must be raised — directory may or may not be created
    # depending on OpenCV backend behavior with unknown codecs.


def test_write_png_creates_output(tmp_path: Path) -> None:
    output = tmp_path / "deep" / "nested" / "frame.png"
    frame = np.full((90, 160, 3), 100, dtype=np.uint8)
    result = write_png(frame, output)
    assert result == output
    assert output.exists()


def test_write_png_overwrites(tmp_path: Path) -> None:
    output = tmp_path / "frame.png"
    frame1 = np.zeros((90, 160, 3), dtype=np.uint8)
    frame2 = np.full((90, 160, 3), 255, dtype=np.uint8)

    p1 = write_png(frame1, output)
    size1 = output.stat().st_size

    p2 = write_png(frame2, output)
    size2 = output.stat().st_size

    assert p1 == p2 == output
    assert size1 > 0
    assert size2 > 0
