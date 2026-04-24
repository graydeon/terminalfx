from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

Frame: TypeAlias = NDArray[np.uint8]


class SourceKind(StrEnum):
    FILE = "file"
    CAMERA = "camera"
    SCREEN = "screen"
    WINDOW = "window"
    MOCK = "mock"


class PreviewMode(StrEnum):
    AUTO = "auto"
    ASCII = "ascii"
    PIXEL = "pixel"


class RenderMode(StrEnum):
    REALTIME = "realtime"
    OFFLINE = "offline"


class TransportStatus(StrEnum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    RECORDING = "recording"


@dataclass(frozen=True, slots=True)
class Resolution:
    width: int = 1920
    height: int = 1080
    fps: int = 60

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0 or self.fps <= 0:
            raise ValueError("resolution width, height, and fps must be positive")


@dataclass(frozen=True, slots=True)
class TimePoint:
    seconds: float = 0.0
    frame: int = 0


@dataclass(frozen=True, slots=True)
class TimeRange:
    start: float
    end: float

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("time range end must be greater than or equal to start")


@dataclass(frozen=True, slots=True)
class FramePacket:
    frame: Frame
    time: TimePoint
    source_name: str
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class AudioFeatures:
    rms: float = 0.0
    peak: float = 0.0
    low: float = 0.0
    mid: float = 0.0
    high: float = 0.0


@dataclass(frozen=True, slots=True)
class WaveformSummary:
    samples: tuple[float, ...]
    sample_rate: int
    duration_seconds: float

    @property
    def peak(self) -> float:
        return max((abs(value) for value in self.samples), default=0.0)
