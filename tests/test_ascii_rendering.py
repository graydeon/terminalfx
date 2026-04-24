import numpy as np

from terminalfx.media.frames import ascii_to_frame


def test_ascii_to_frame_spans_canvas_width() -> None:
    ascii_frame = "\n".join(["#" * 32 for _ in range(18)])

    frame = ascii_to_frame(ascii_frame, width=320, height=180)
    mask = np.any(frame > 0, axis=2)
    cols = np.where(mask.any(axis=0))[0]

    assert cols.size > 0
    assert cols[-1] - cols[0] > 260
