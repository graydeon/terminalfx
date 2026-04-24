import numpy as np

from terminalfx.core.types import PreviewMode, Resolution, TimePoint
from terminalfx.effects.base import EffectContext
from terminalfx.effects.stack import EffectNode, EffectStack


def test_effect_stack_applies_enabled_nodes_in_order() -> None:
    frame = np.full((8, 8, 3), 120, dtype=np.uint8)
    stack = EffectStack(
        [
            EffectNode("ascii_quantize", params={"levels": 2, "contrast": 1.0}),
            EffectNode(
                "terminal_tint", params={"palette": "green", "scanlines": False, "intensity": 1.0}
            ),
        ]
    )

    result = stack.apply(
        frame,
        EffectContext(Resolution(8, 8, 24), TimePoint(), preview_mode=PreviewMode.PIXEL),
    )

    assert result.shape == frame.shape
    assert result[:, :, 1].mean() >= result[:, :, 0].mean()


def test_bypassed_effect_is_not_applied() -> None:
    frame = np.full((4, 4, 3), 100, dtype=np.uint8)
    stack = EffectStack([EffectNode("terminal_tint", enabled=False)])

    result = stack.apply(frame, EffectContext(Resolution(4, 4, 24), TimePoint()))

    assert np.array_equal(result, frame)


def test_ascii_brightness_parameter_changes_output() -> None:
    frame = np.full((8, 8, 3), 80, dtype=np.uint8)
    context = EffectContext(Resolution(8, 8, 24), TimePoint())

    dark = EffectStack(
        [EffectNode("ascii_quantize", params={"levels": 24, "brightness": -40.0})]
    ).apply(frame, context)
    bright = EffectStack(
        [EffectNode("ascii_quantize", params={"levels": 24, "brightness": 40.0})]
    ).apply(frame, context)

    assert bright.mean() > dark.mean()


def test_duplicate_gets_new_node_id() -> None:
    stack = EffectStack([EffectNode("passthrough")])

    duplicate = stack.duplicate(0)

    assert duplicate.node_id != stack.nodes[0].node_id
    assert len(stack.nodes) == 2
