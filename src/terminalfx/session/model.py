from __future__ import annotations

from dataclasses import dataclass, field

from terminalfx.config.schema import ProjectConfig
from terminalfx.core.types import PreviewMode, RenderMode, TransportStatus
from terminalfx.effects.stack import EffectNode, EffectStack


@dataclass(slots=True)
class ExportJob:
    kind: str
    path: str
    render_mode: RenderMode
    status: str = "queued"


@dataclass(slots=True)
class SessionState:
    project: ProjectConfig
    effect_stack: EffectStack = field(default_factory=EffectStack)
    selected_effect_index: int = 0
    preview_mode: PreviewMode = PreviewMode.AUTO
    transport_status: TransportStatus = TransportStatus.STOPPED
    playhead_seconds: float = 0.0
    recording_armed: bool = False
    export_queue: list[ExportJob] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    @classmethod
    def from_project(cls, project: ProjectConfig) -> SessionState:
        stack = EffectStack.from_config(project.effects)
        if not stack.nodes:
            stack.add("ascii_quantize")
            stack.add("terminal_tint")
        return cls(project=project, effect_stack=stack, preview_mode=project.preview.mode)

    @property
    def selected_effect(self) -> EffectNode | None:
        if not self.effect_stack.nodes:
            return None
        self.selected_effect_index = min(
            self.selected_effect_index, len(self.effect_stack.nodes) - 1
        )
        return self.effect_stack.nodes[self.selected_effect_index]

    def append_log(self, message: str) -> None:
        self.log.append(message)
        del self.log[:-200]
