from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from terminalfx.core.types import FramePacket, SourceKind, TimePoint


@dataclass(frozen=True, slots=True)
class SourceCapabilities:
    seekable: bool
    live: bool
    has_audio: bool = False


@dataclass(frozen=True, slots=True)
class SourceInfo:
    kind: SourceKind
    name: str
    width: int
    height: int
    fps: float
    duration_seconds: float | None = None
    capabilities: SourceCapabilities = SourceCapabilities(seekable=False, live=True)


class SourceProvider(Protocol):
    def open(self) -> SourceInfo:
        """Open the source and return metadata."""

    def read(self, time: TimePoint | None = None) -> FramePacket | None:
        """Return the next frame packet, or None on EOF."""

    def seek(self, time: TimePoint) -> None:
        """Seek to a time point when supported."""

    def close(self) -> None:
        """Release source resources."""
