from __future__ import annotations

from terminalfx.config.schema import SourceConfig
from terminalfx.core.errors import SourceError
from terminalfx.core.types import Resolution, SourceKind
from terminalfx.sources.base import SourceProvider
from terminalfx.sources.camera import CameraSource
from terminalfx.sources.mock import MockSource
from terminalfx.sources.screen import ScreenSource, WindowSource
from terminalfx.sources.video_file import VideoFileSource


def create_source(config: SourceConfig, resolution: Resolution) -> SourceProvider:
    if config.kind == SourceKind.MOCK:
        return MockSource(resolution)
    if config.kind == SourceKind.FILE:
        if config.path is None:
            raise SourceError("file source requires a path")
        return VideoFileSource(config.path, loop=config.loop)
    if config.kind == SourceKind.CAMERA:
        return CameraSource(
            config.camera_index,
            target_width=resolution.width,
            target_height=resolution.height,
            target_fps=resolution.fps,
        )
    if config.kind == SourceKind.SCREEN:
        return ScreenSource(config.screen_index, fps=float(resolution.fps))
    if config.kind == SourceKind.WINDOW:
        if not config.window_title:
            raise SourceError("window source requires a title")
        return WindowSource(config.window_title, fps=float(resolution.fps))
    raise SourceError(f"unsupported source kind: {config.kind}")
