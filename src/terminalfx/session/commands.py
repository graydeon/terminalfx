from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from terminalfx.core.types import PreviewMode, SourceKind, TransportStatus


@dataclass(frozen=True, slots=True)
class Command:
    pass


@dataclass(frozen=True, slots=True)
class SetSource(Command):
    kind: SourceKind


@dataclass(frozen=True, slots=True)
class SetPreviewMode(Command):
    mode: PreviewMode


@dataclass(frozen=True, slots=True)
class SetTransport(Command):
    status: TransportStatus


@dataclass(frozen=True, slots=True)
class AddEffect(Command):
    type_name: str


@dataclass(frozen=True, slots=True)
class RemoveSelectedEffect(Command):
    pass


@dataclass(frozen=True, slots=True)
class SelectEffect(Command):
    delta: int


@dataclass(frozen=True, slots=True)
class MoveSelectedEffect(Command):
    delta: int


@dataclass(frozen=True, slots=True)
class ToggleSelectedEffect(Command):
    pass


@dataclass(frozen=True, slots=True)
class DuplicateSelectedEffect(Command):
    pass


@dataclass(frozen=True, slots=True)
class SaveSelectedEffectPreset(Command):
    path: Path


@dataclass(frozen=True, slots=True)
class LoadEffectPreset(Command):
    path: Path


@dataclass(frozen=True, slots=True)
class SetEffectParameter(Command):
    index: int
    name: str
    value: object


@dataclass(frozen=True, slots=True)
class QueueExport(Command):
    kind: str
