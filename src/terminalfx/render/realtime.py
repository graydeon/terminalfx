from __future__ import annotations

from pathlib import Path
from time import monotonic, sleep

from terminalfx.config.schema import ProjectConfig
from terminalfx.render.encoders import Mp4Encoder
from terminalfx.render.pipeline import RenderPipeline


def record_realtime(
    pipeline: RenderPipeline, config: ProjectConfig, path: Path, seconds: float
) -> Path:
    resolution = config.resolution
    frame_limit = max(1, int(seconds * resolution.fps))
    frame_interval = 1.0 / resolution.fps
    next_frame_at = monotonic()
    with Mp4Encoder(
        path, resolution.width, resolution.height, resolution.fps, config.output.codec
    ) as encoder:
        for _ in range(frame_limit):
            packet = pipeline.render_next()
            if packet is None:
                break
            encoder.write(packet.frame)
            next_frame_at += frame_interval
            delay = next_frame_at - monotonic()
            if delay > 0:
                sleep(delay)
    return path
