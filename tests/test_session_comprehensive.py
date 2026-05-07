"""Tests for session state, export queue, source cycling, and preset round-trips."""

from pathlib import Path

from terminalfx.config.schema import ProjectConfig
from terminalfx.core.types import PreviewMode, SourceKind, TransportStatus
from terminalfx.session import commands as cmd
from terminalfx.session.controller import SessionController
from terminalfx.session.model import SessionState


def test_session_from_project_adds_default_effects() -> None:
    project = ProjectConfig()
    state = SessionState.from_project(project)
    assert len(state.effect_stack.nodes) >= 2
    types = {n.type_name for n in state.effect_stack.nodes}
    assert "ascii_quantize" in types
    assert "terminal_tint" in types


def test_controller_toggle_play_cycles() -> None:
    state = SessionState.from_project(ProjectConfig())
    ctrl = SessionController(state)

    assert state.transport_status == TransportStatus.STOPPED
    ctrl.toggle_play()
    assert state.transport_status == TransportStatus.PLAYING
    ctrl.toggle_play()
    assert state.transport_status == TransportStatus.PAUSED


def test_controller_cycle_source_advances_kind() -> None:
    state = SessionState.from_project(ProjectConfig())
    ctrl = SessionController(state)

    assert state.project.source.kind == SourceKind.MOCK
    ctrl.cycle_source_kind()
    assert state.project.source.kind == SourceKind.FILE


def test_controller_queue_export_appends_job() -> None:
    state = SessionState.from_project(ProjectConfig())
    ctrl = SessionController(state)

    ctrl.dispatch(cmd.QueueExport("png"))
    assert len(state.export_queue) == 1
    assert state.export_queue[0].kind == "png"
    assert state.export_queue[0].status == "queued"

    ctrl.dispatch(cmd.QueueExport("mp4"))
    assert len(state.export_queue) == 2
    assert state.export_queue[1].kind == "mp4"


def test_controller_add_effect_cycles_types() -> None:
    state = SessionState.from_project(ProjectConfig())
    ctrl = SessionController(state)
    initial_count = len(state.effect_stack.nodes)

    ctrl.dispatch(cmd.AddEffect("phosphor_trail"))
    assert len(state.effect_stack.nodes) == initial_count + 1

    ctrl.dispatch(cmd.AddEffect("terminal_tint"))
    assert len(state.effect_stack.nodes) == initial_count + 2


def test_preset_save_and_load(tmp_path: Path) -> None:
    state = SessionState.from_project(ProjectConfig())
    ctrl = SessionController(state)

    # Select first effect and set a param
    state.selected_effect_index = 0
    state.effect_stack.nodes[0].params["intensity"] = 0.75

    presets_dir = tmp_path / "presets"
    presets_dir.mkdir()
    preset_path = presets_dir / "test-preset.yaml"

    ctrl.dispatch(cmd.SaveSelectedEffectPreset(preset_path))
    assert preset_path.exists()

    # Clear state and reload
    initial_count = len(state.effect_stack.nodes)
    ctrl.dispatch(cmd.LoadEffectPreset(preset_path))
    assert len(state.effect_stack.nodes) == initial_count + 1


def test_listener_notified_on_dispatch() -> None:
    state = SessionState.from_project(ProjectConfig())
    ctrl = SessionController(state)

    calls = []
    ctrl.subscribe(lambda s: calls.append(1))

    ctrl.dispatch(cmd.SetPreviewMode(PreviewMode.PIXEL))
    assert len(calls) == 1

    ctrl.dispatch(cmd.SetSource(SourceKind.MOCK))
    assert len(calls) == 2


def test_toggle_record_arm_flips() -> None:
    state = SessionState.from_project(ProjectConfig())
    ctrl = SessionController(state)

    assert not state.recording_armed
    ctrl.toggle_record_arm()
    assert state.recording_armed
    ctrl.toggle_record_arm()
    assert not state.recording_armed
