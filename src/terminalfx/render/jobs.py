from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from terminalfx.config.schema import ProjectConfig
from terminalfx.core.types import RenderMode


@dataclass(frozen=True, slots=True)
class RenderJob:
    kind: str
    path: Path
    mode: RenderMode
    frame_limit: int = 180

    @classmethod
    def png(cls, config: ProjectConfig) -> RenderJob:
        return cls(
            kind="png", path=config.output.image_path, mode=config.output.render_mode, frame_limit=1
        )

    @classmethod
    def mp4(cls, config: ProjectConfig, frame_limit: int = 180) -> RenderJob:
        return cls(
            kind="mp4",
            path=config.output.video_path,
            mode=config.output.render_mode,
            frame_limit=frame_limit,
        )
