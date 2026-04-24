from __future__ import annotations

from typing import Any, cast

import cv2
import numpy as np

from terminalfx.core.types import Frame
from terminalfx.effects.base import EffectContext
from terminalfx.effects.params import ParameterSchema, ParameterSpec


class PassthroughEffect:
    type_name = "passthrough"
    display_name = "Passthrough"
    parameters = ParameterSchema(())

    def apply(self, frame: Frame, params: dict[str, object], context: EffectContext) -> Frame:
        return frame.copy()


class TerminalTintEffect:
    type_name = "terminal_tint"
    display_name = "Terminal Tint"
    parameters = ParameterSchema(
        (
            ParameterSpec(
                "palette",
                "enum",
                "green",
                options=("green", "amber", "white", "cyan"),
            ),
            ParameterSpec("scanlines", "bool", True),
            ParameterSpec("intensity", "float", 1.0, minimum=0.0, maximum=1.0, step=0.05),
        )
    )

    _palettes = {
        "green": np.array([90, 255, 120], dtype=np.float32),
        "amber": np.array([255, 191, 64], dtype=np.float32),
        "white": np.array([230, 240, 255], dtype=np.float32),
        "cyan": np.array([90, 220, 255], dtype=np.float32),
    }

    def apply(self, frame: Frame, params: dict[str, object], context: EffectContext) -> Frame:
        palette = self._palettes[str(params["palette"])]
        gray = frame.mean(axis=2, keepdims=True).astype(np.float32) / 255.0
        tinted = gray * palette
        intensity = _float_param(params["intensity"])
        mixed = frame.astype(np.float32) * (1.0 - intensity) + tinted * intensity
        result = np.clip(mixed, 0, 255).astype(np.uint8)
        if bool(params["scanlines"]):
            result[::2] = (result[::2].astype(np.float32) * 0.72).astype(np.uint8)
        return cast(Frame, result)


class AsciiQuantizeEffect:
    type_name = "ascii_quantize"
    display_name = "ASCII Quantize"
    parameters = ParameterSchema(
        (
            ParameterSpec("levels", "int", 9, minimum=2, maximum=24, step=1),
            ParameterSpec("invert", "bool", False),
            ParameterSpec("contrast", "float", 1.15, minimum=0.2, maximum=3.0, step=0.05),
            ParameterSpec("brightness", "float", 0.0, minimum=-80.0, maximum=80.0, step=2.0),
        )
    )

    def apply(self, frame: Frame, params: dict[str, object], context: EffectContext) -> Frame:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        gray = np.clip(
            (gray - 127.5) * _float_param(params["contrast"])
            + 127.5
            + _float_param(params["brightness"]),
            0,
            255,
        )
        levels = _int_param(params["levels"])
        step = 255.0 / max(1, levels - 1)
        quantized = np.round(gray / step) * step
        if bool(params["invert"]):
            quantized = 255 - quantized
        result = cv2.cvtColor(np.clip(quantized, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        return cast(Frame, result)


class PhosphorTrailEffect:
    type_name = "phosphor_trail"
    display_name = "Phosphor Trail"
    parameters = ParameterSchema(
        (
            ParameterSpec("blend", "float", 0.18, minimum=0.0, maximum=0.9, step=0.01),
            ParameterSpec("decay", "float", 0.86, minimum=0.0, maximum=1.0, step=0.01),
        )
    )

    def __init__(self) -> None:
        self._previous: Frame | None = None

    def apply(self, frame: Frame, params: dict[str, object], context: EffectContext) -> Frame:
        if self._previous is None or self._previous.shape != frame.shape:
            self._previous = frame.copy()
            return frame.copy()
        blend = _float_param(params["blend"])
        decay = _float_param(params["decay"])
        trailed = cv2.addWeighted(frame, 1.0 - blend, self._previous, blend, 0)
        self._previous = np.clip(trailed.astype(np.float32) * decay, 0, 255).astype(np.uint8)
        return cast(Frame, trailed)


def _float_param(value: object) -> float:
    return float(cast(Any, value))


def _int_param(value: object) -> int:
    return int(cast(Any, value))
