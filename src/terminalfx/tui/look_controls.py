"""Look slider control logic for the terminalfx TUI.

Manages the density/contrast/brightness/levels/tint slider system
that provides keyboard-driven parameter adjustments.
"""

from typing import Any, cast

from terminalfx.effects.stack import EffectNode
from terminalfx.session.model import SessionState

# Slider: (label, value, minimum, maximum, step)
SliderDef = tuple[str, float, float, float, float]
LookControls = list[SliderDef]

SLIDER_WIDTH = 18


def build_look_controls(state: SessionState) -> LookControls:
    """Build slider definitions from the current session state."""
    ascii_node = _first_effect_node(state, "ascii_quantize")
    tint_node = _first_effect_node(state, "terminal_tint")
    preview = state.project.preview
    return [
        ("density", float(preview.character_width), 80.0, 320.0, 8.0),
        ("contrast", _param(ascii_node, "contrast", 1.15), 0.2, 3.0, 0.05),
        ("brightness", _param(ascii_node, "brightness", 0.0), -80.0, 80.0, 2.0),
        ("levels", _param(ascii_node, "levels", 9.0), 2.0, 24.0, 1.0),
        ("tint", _param(tint_node, "intensity", 0.85), 0.0, 1.0, 0.05),
    ]


def render_slider_lines(
    controls: LookControls,
    active_index: int,
) -> list[str]:
    """Render slider bar strings for the params panel."""
    return [
        _slider_line(index, label, value, minimum, maximum, active_index)
        for index, (label, value, minimum, maximum, _step) in enumerate(controls)
    ]


def _slider_line(
    index: int,
    label: str,
    value: float,
    minimum: float,
    maximum: float,
    active_index: int,
) -> str:
    normalized = 0.0 if maximum == minimum else (value - minimum) / (maximum - minimum)
    marker = max(0, min(SLIDER_WIDTH - 1, round(normalized * (SLIDER_WIDTH - 1))))
    cells = ["-"] * SLIDER_WIDTH
    cells[marker] = "|"
    prefix = ">" if index == active_index else " "
    return f"{prefix} {label:<10} [{''.join(cells)}] {value:g}"


def adjust_look_control(state: SessionState, direction: int, active_index: int) -> None:
    """Apply a ±1 step to the active slider control."""
    controls = build_look_controls(state)
    active_index %= len(controls)
    label, value, minimum, maximum, step = controls[active_index]
    next_value = max(minimum, min(maximum, value + step * direction))

    if label == "density":
        width = int(round(next_value / 8.0) * 8)
        state.project.preview.character_width = width
        state.project.preview.character_height = max(1, round(width * 9 / 16))
        state.append_log(
            "density: "
            f"{state.project.preview.character_width}x"
            f"{state.project.preview.character_height}"
        )
        return

    if label in {"contrast", "brightness", "levels"}:
        node = _first_effect_node(state, "ascii_quantize")
        if node is not None:
            node.params[label] = int(next_value) if label == "levels" else round(next_value, 2)
            state.append_log(f"{label}: {node.params[label]}")
        return

    if label == "tint":
        node = _first_effect_node(state, "terminal_tint")
        if node is not None:
            node.params["intensity"] = round(next_value, 2)
            state.append_log(f"tint intensity: {node.params['intensity']}")


def _first_effect_node(state: SessionState, type_name: str) -> EffectNode | None:
    for node in state.effect_stack.nodes:
        if node.type_name == type_name:
            return node
    return None


def _param(node: EffectNode | None, name: str, default: float) -> float:
    if node is None:
        return default
    value = node.params.get(name, default)
    return float(cast(Any, value))
