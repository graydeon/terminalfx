"""Tests for effect parameter validation, registry, and edge cases."""

import pytest

from terminalfx.core.errors import EffectError
from terminalfx.effects.registry import default_effect_registry
from terminalfx.effects.stack import EffectNode, EffectStack


def test_unknown_effect_raises() -> None:
    registry = default_effect_registry()
    with pytest.raises(EffectError):
        registry.create("nonexistent_effect")


def test_unknown_effect_in_stack_add_falls_back_to_passthrough() -> None:
    """Controller._add_effect catches EffectError and falls back to passthrough."""
    from terminalfx.config.schema import ProjectConfig
    from terminalfx.session import commands as cmd
    from terminalfx.session.controller import SessionController
    from terminalfx.session.model import SessionState

    state = SessionState.from_project(ProjectConfig())
    ctrl = SessionController(state)

    ctrl.dispatch(cmd.AddEffect("bogus_effect"))
    added = state.effect_stack.nodes[-1]
    assert added.type_name == "passthrough"
    assert added.label == "bogus_effect"


def test_registry_names_includes_all_registered() -> None:
    registry = default_effect_registry()
    names = registry.names()
    assert "passthrough" in names
    assert "ascii_quantize" in names
    assert "terminal_tint" in names
    assert "phosphor_trail" in names


def test_node_id_preserved_in_round_trip() -> None:
    node = EffectNode("terminal_tint", params={"intensity": 0.5})
    stack = EffectStack([node])

    config = stack.to_config()
    restored = EffectStack.from_config(config, stack.registry)

    assert len(restored.nodes) == 1
    assert restored.nodes[0].node_id == node.node_id
    assert restored.nodes[0].type_name == "terminal_tint"
    assert restored.nodes[0].params["intensity"] == 0.5


def test_node_id_generated_when_not_in_config() -> None:
    config = [{"type": "passthrough", "enabled": True}]
    stack = EffectStack.from_config(config)
    assert len(stack.nodes) == 1
    assert stack.nodes[0].node_id  # should be auto-generated
    assert len(stack.nodes[0].node_id) > 0


def test_to_config_includes_node_id() -> None:
    stack = EffectStack([EffectNode("passthrough")])
    config = stack.to_config()
    assert "node_id" in config[0]
    assert config[0]["node_id"] == stack.nodes[0].node_id


def test_duplicate_gets_new_node_id() -> None:
    stack = EffectStack([EffectNode("passthrough")])
    duplicate = stack.duplicate(0)

    assert duplicate.node_id != stack.nodes[0].node_id
    assert len(stack.nodes) == 2
