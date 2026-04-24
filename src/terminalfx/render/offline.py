from __future__ import annotations

from pathlib import Path

from terminalfx.config.schema import ProjectConfig
from terminalfx.render.encoders import Mp4Encoder, write_png
from terminalfx.render.pipeline import RenderPipeline


def render_png(pipeline: RenderPipeline, path: Path) -> Path:
    packet = pipeline.render_next()
    if packet is None:
        raise RuntimeError("source produced no frames")
    return write_png(packet.frame, path)


def render_mp4(pipeline: RenderPipeline, config: ProjectConfig, path: Path, frames: int) -> Path:
    resolution = config.resolution
    with Mp4Encoder(
        path, resolution.width, resolution.height, resolution.fps, config.output.codec
    ) as encoder:
        for _ in range(frames):
            packet = pipeline.render_next()
            if packet is None:
                break
            encoder.write(packet.frame)
    return path
