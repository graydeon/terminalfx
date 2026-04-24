from pathlib import Path

from terminalfx.config.schema import ProjectConfig
from terminalfx.session import commands as cmd
from terminalfx.session.controller import SessionController
from terminalfx.session.model import SessionState


def test_session_controller_edits_stack_and_selection() -> None:
    controller = SessionController(SessionState.from_project(ProjectConfig()))

    controller.dispatch(cmd.AddEffect("phosphor_trail"))
    controller.dispatch(cmd.MoveSelectedEffect(-1))
    controller.dispatch(cmd.ToggleSelectedEffect())

    state = controller.state
    assert state.selected_effect is not None
    assert state.selected_effect.type_name == "phosphor_trail"
    assert state.selected_effect.enabled is False


def test_save_and_load_selected_effect_preset(tmp_path: Path) -> None:
    controller = SessionController(SessionState.from_project(ProjectConfig()))
    preset_path = tmp_path / "preset.yaml"

    controller.dispatch(cmd.SaveSelectedEffectPreset(preset_path))
    controller.dispatch(cmd.LoadEffectPreset(preset_path))

    assert preset_path.exists()
    assert len(controller.state.effect_stack.nodes) == 3
