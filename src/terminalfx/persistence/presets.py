from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from terminalfx.effects.stack import EffectNode


def save_effect_preset(node: EffectNode, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "effect": {
            "type": node.type_name,
            "enabled": node.enabled,
            "params": dict(node.params),
            "label": node.label,
        },
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def load_effect_preset(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text()) or {}
    if int(payload.get("schema_version", 1)) != 1:
        raise ValueError("unsupported preset schema_version")
    effect = payload.get("effect")
    if not isinstance(effect, dict):
        raise ValueError("preset does not contain an effect")
    return effect
