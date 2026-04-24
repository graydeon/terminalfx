from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from terminalfx.core.types import AudioFeatures, Frame, PreviewMode, Resolution, TimePoint
from terminalfx.effects.params import ParameterSchema


@dataclass(frozen=True, slots=True)
class EffectContext:
    resolution: Resolution
    time: TimePoint
    preview_mode: PreviewMode = PreviewMode.AUTO
    audio: AudioFeatures = AudioFeatures()


class Effect(Protocol):
    type_name: str
    display_name: str
    parameters: ParameterSchema

    def apply(self, frame: Frame, params: dict[str, object], context: EffectContext) -> Frame:
        """Return a transformed frame."""
