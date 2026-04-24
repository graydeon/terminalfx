from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any

from terminalfx.config.loader import to_plain_data
from terminalfx.config.schema import ProjectConfig
from terminalfx.session.model import SessionState


@dataclass(frozen=True, slots=True)
class PreviewSnapshot:
    timestamp: float
    project_name: str
    project: dict[str, Any]
    preview_mode: str
    transport_status: str
    selected_effect_index: int
    effects: list[dict[str, object]]
    recording_armed: bool

    @classmethod
    def from_session(cls, state: SessionState) -> PreviewSnapshot:
        return cls(
            timestamp=time(),
            project_name=state.project.project_name,
            project=to_plain_data(state.project),
            preview_mode=str(state.preview_mode),
            transport_status=str(state.transport_status),
            selected_effect_index=state.selected_effect_index,
            effects=state.effect_stack.to_config(),
            recording_armed=state.recording_armed,
        )


def project_from_snapshot(snapshot: dict[str, Any], fallback: ProjectConfig) -> ProjectConfig:
    """Apply the session-owned fields a preview process needs over its startup config."""
    project = fallback
    if "effects" in snapshot:
        project.effects = list(snapshot["effects"])
    preview_mode = snapshot.get("preview_mode")
    if preview_mode is not None:
        project.preview.mode = type(project.preview.mode)(str(preview_mode))
    project.source.kind = type(project.source.kind)(
        str(snapshot.get("project", {}).get("source", {}).get("kind", project.source.kind))
    )
    return project
