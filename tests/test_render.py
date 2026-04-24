from pathlib import Path

import numpy as np

from terminalfx.config.schema import ProjectConfig, SourceConfig
from terminalfx.core.types import Resolution, SourceKind
from terminalfx.effects.stack import EffectStack
from terminalfx.media.frames import normalize_frame
from terminalfx.render.offline import render_png
from terminalfx.render.pipeline import RenderPipeline
from terminalfx.sources import create_source


def test_mock_source_renders_png(tmp_path: Path) -> None:
    project = ProjectConfig(
        resolution=Resolution(160, 90, 24),
        source=SourceConfig(kind=SourceKind.MOCK),
        effects=[{"type": "terminal_tint", "enabled": True, "params": {"intensity": 0.5}}],
    )
    source = create_source(project.source, project.resolution)
    source.open()
    try:
        pipeline = RenderPipeline(source, EffectStack.from_config(project.effects), project)
        out_path = render_png(pipeline, tmp_path / "frame.png")
    finally:
        source.close()

    assert out_path.exists()
    assert out_path.stat().st_size > 0


def test_normalize_frame_preserves_aspect_by_cropping_to_fill() -> None:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    frame[:, :40] = (255, 0, 0)
    frame[:, 120:] = (0, 0, 255)

    normalized = normalize_frame(frame, 160, 90)

    assert normalized.shape == (90, 160, 3)
    assert normalized[:, :8].mean() > 0
