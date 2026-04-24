from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from terminalfx.core.types import PreviewMode, RenderMode, Resolution, SourceKind


@dataclass(slots=True)
class SourceConfig:
    kind: SourceKind = SourceKind.MOCK
    path: Path | None = None
    camera_index: int = 0
    screen_index: int = 0
    window_title: str | None = None
    loop: bool = True


@dataclass(slots=True)
class PreviewConfig:
    enabled: bool = True
    mode: PreviewMode = PreviewMode.AUTO
    display_index: int = 1
    fullscreen: bool = True
    refresh_hz: int = 60
    character_width: int = 160
    character_height: int = 90
    transport_path: Path = Path("run/preview-state.json")


@dataclass(slots=True)
class OutputConfig:
    directory: Path = Path("output")
    video_path: Path = Path("output/render.mp4")
    image_path: Path = Path("output/frame.png")
    codec: str = "mp4v"
    render_mode: RenderMode = RenderMode.OFFLINE


@dataclass(slots=True)
class AudioConfig:
    enabled: bool = True
    waveform_resolution: int = 128
    analysis_window_seconds: float = 1.0


@dataclass(slots=True)
class ProjectConfig:
    schema_version: int = 1
    project_name: str = "terminalfx"
    resolution: Resolution = field(default_factory=Resolution)
    source: SourceConfig = field(default_factory=SourceConfig)
    preview: PreviewConfig = field(default_factory=PreviewConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    effects: list[dict[str, Any]] = field(default_factory=list)

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"unsupported project schema_version: {self.schema_version}")
        if self.preview.refresh_hz <= 0:
            raise ValueError("preview refresh_hz must be positive")
        if self.preview.character_width <= 0 or self.preview.character_height <= 0:
            raise ValueError("preview character dimensions must be positive")
        if self.audio.waveform_resolution <= 0:
            raise ValueError("audio waveform_resolution must be positive")
