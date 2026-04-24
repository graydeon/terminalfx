from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from terminalfx.core.errors import EffectError
from terminalfx.core.types import PreviewMode, SourceKind, TransportStatus
from terminalfx.effects.stack import EffectNode
from terminalfx.persistence.presets import load_effect_preset, save_effect_preset
from terminalfx.session import commands as cmd
from terminalfx.session.model import ExportJob, SessionState

SessionListener = Callable[[SessionState], None]


class SessionController:
    """Single authority for mutating session state."""

    def __init__(self, state: SessionState) -> None:
        self.state = state
        self._listeners: list[SessionListener] = []

    def subscribe(self, listener: SessionListener) -> None:
        self._listeners.append(listener)

    def dispatch(self, command: cmd.Command) -> SessionState:
        if isinstance(command, cmd.SetSource):
            self._set_source(command.kind)
        elif isinstance(command, cmd.SetPreviewMode):
            self.state.preview_mode = command.mode
            self.state.append_log(f"preview mode: {command.mode}")
        elif isinstance(command, cmd.SetTransport):
            self.state.transport_status = command.status
            self.state.append_log(f"transport: {command.status}")
        elif isinstance(command, cmd.AddEffect):
            self._add_effect(command.type_name)
        elif isinstance(command, cmd.RemoveSelectedEffect):
            self._remove_selected()
        elif isinstance(command, cmd.SelectEffect):
            self._select(command.delta)
        elif isinstance(command, cmd.MoveSelectedEffect):
            self._move(command.delta)
        elif isinstance(command, cmd.ToggleSelectedEffect):
            self._toggle_selected()
        elif isinstance(command, cmd.DuplicateSelectedEffect):
            self._duplicate_selected()
        elif isinstance(command, cmd.SaveSelectedEffectPreset):
            self._save_selected_preset(command.path)
        elif isinstance(command, cmd.LoadEffectPreset):
            self._load_preset(command.path)
        elif isinstance(command, cmd.SetEffectParameter):
            self._set_parameter(command.index, command.name, command.value)
        elif isinstance(command, cmd.QueueExport):
            self._queue_export(command.kind)
        else:
            raise TypeError(f"unsupported command: {command!r}")
        self._notify()
        return self.state

    def cycle_preview_mode(self) -> SessionState:
        modes = list(PreviewMode)
        index = modes.index(self.state.preview_mode)
        return self.dispatch(cmd.SetPreviewMode(modes[(index + 1) % len(modes)]))

    def cycle_source_kind(self) -> SessionState:
        kinds = [
            SourceKind.MOCK,
            SourceKind.FILE,
            SourceKind.CAMERA,
            SourceKind.SCREEN,
            SourceKind.WINDOW,
        ]
        index = kinds.index(self.state.project.source.kind)
        return self.dispatch(cmd.SetSource(kinds[(index + 1) % len(kinds)]))

    def toggle_play(self) -> SessionState:
        next_status = (
            TransportStatus.PAUSED
            if self.state.transport_status == TransportStatus.PLAYING
            else TransportStatus.PLAYING
        )
        return self.dispatch(cmd.SetTransport(next_status))

    def toggle_record_arm(self) -> SessionState:
        self.state.recording_armed = not self.state.recording_armed
        self.state.append_log(f"record armed: {self.state.recording_armed}")
        self._notify()
        return self.state

    def _set_source(self, kind: SourceKind) -> None:
        self.state.project.source.kind = kind
        self.state.append_log(f"source: {kind}")

    def _add_effect(self, type_name: str) -> None:
        try:
            node = self.state.effect_stack.add(type_name)
        except EffectError:
            node = self.state.effect_stack.add("passthrough")
            node.label = type_name
        self.state.selected_effect_index = len(self.state.effect_stack.nodes) - 1
        self.state.append_log(f"effect added: {node.type_name}")

    def _remove_selected(self) -> None:
        if len(self.state.effect_stack.nodes) <= 1:
            self.state.append_log("cannot remove last effect")
            return
        removed = self.state.effect_stack.remove(self.state.selected_effect_index)
        self.state.selected_effect_index = min(
            self.state.selected_effect_index,
            len(self.state.effect_stack.nodes) - 1,
        )
        self.state.append_log(f"effect removed: {removed.type_name}")

    def _select(self, delta: int) -> None:
        if not self.state.effect_stack.nodes:
            return
        self.state.selected_effect_index = max(
            0,
            min(self.state.selected_effect_index + delta, len(self.state.effect_stack.nodes) - 1),
        )

    def _move(self, delta: int) -> None:
        old = self.state.selected_effect_index
        new = max(0, min(old + delta, len(self.state.effect_stack.nodes) - 1))
        if old == new:
            return
        self.state.effect_stack.move(old, new)
        self.state.selected_effect_index = new
        self.state.append_log(f"effect moved: {old} -> {new}")

    def _toggle_selected(self) -> None:
        node = self.state.selected_effect
        if node is None:
            return
        node.enabled = not node.enabled
        self.state.append_log(f"effect enabled: {node.enabled}")

    def _duplicate_selected(self) -> None:
        node = self.state.effect_stack.duplicate(self.state.selected_effect_index)
        self.state.selected_effect_index += 1
        self.state.append_log(f"effect duplicated: {node.type_name}")

    def _save_selected_preset(self, path: Path) -> None:
        node = self.state.selected_effect
        if node is None:
            return
        save_effect_preset(node, path)
        self.state.append_log(f"preset saved: {path}")

    def _load_preset(self, path: Path) -> None:
        effect = load_effect_preset(path)
        node = EffectNode(
            type_name=str(effect.get("type", "passthrough")),
            enabled=bool(effect.get("enabled", True)),
            params=dict(effect.get("params", {})),
            label=str(effect["label"]) if effect.get("label") else None,
        )
        insert_at = min(self.state.selected_effect_index + 1, len(self.state.effect_stack.nodes))
        self.state.effect_stack.nodes.insert(insert_at, node)
        self.state.selected_effect_index = insert_at
        self.state.append_log(f"preset loaded: {path}")

    def _set_parameter(self, index: int, name: str, value: object) -> None:
        node = self.state.effect_stack.nodes[index]
        node.params[name] = value
        self.state.append_log(f"parameter set: {node.type_name}.{name}")

    def _queue_export(self, kind: str) -> None:
        output = self.state.project.output
        path = str(output.image_path if kind == "png" else output.video_path)
        self.state.export_queue.append(
            ExportJob(kind=kind, path=path, render_mode=output.render_mode)
        )
        self.state.append_log(f"export queued: {path}")

    def _notify(self) -> None:
        for listener in self._listeners:
            listener(self.state)
