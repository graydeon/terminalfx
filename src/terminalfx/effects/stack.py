from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from terminalfx.core.types import Frame
from terminalfx.effects.base import Effect as _Effect
from terminalfx.effects.base import EffectContext
from terminalfx.effects.registry import EffectRegistry, default_effect_registry


@dataclass(slots=True)
class EffectNode:
    type_name: str
    params: dict[str, object] = field(default_factory=dict)
    enabled: bool = True
    label: str | None = None
    node_id: str = field(default_factory=lambda: uuid4().hex)
    # Cache: (params_hash, validated_params) to avoid re-validation every frame
    _cached_params_hash: int = 0
    _cached_params: dict[str, object] | None = field(default=None, repr=False)

    def duplicate(self) -> EffectNode:
        return EffectNode(
            type_name=self.type_name,
            params=dict(self.params),
            enabled=self.enabled,
            label=self.label,
        )


class EffectStack:
    def __init__(
        self,
        nodes: list[EffectNode] | None = None,
        registry: EffectRegistry | None = None,
    ) -> None:
        self.registry = registry or default_effect_registry()
        self.nodes = nodes or []
        self._instances: dict[str, _Effect] = {
            node.node_id: self.registry.create(node.type_name) for node in self.nodes
        }

    @classmethod
    def from_config(
        cls,
        payload: list[dict[str, object]],
        registry: EffectRegistry | None = None,
    ) -> EffectStack:
        nodes: list[EffectNode] = []
        for item in payload:
            type_name = str(item.get("type", item.get("type_name", "passthrough")))
            raw_params = item.get("params", {})
            params = dict(raw_params) if isinstance(raw_params, dict) else {}
            node_id = item.get("node_id")
            node = EffectNode(
                type_name=type_name,
                params=params,
                enabled=bool(item.get("enabled", True)),
                label=str(item["label"]) if item.get("label") else None,
            )
            if node_id and isinstance(node_id, str) and node_id.strip():
                node.node_id = node_id.strip()
            nodes.append(node)
        return cls(nodes, registry)

    def apply(self, frame: Frame, context: EffectContext) -> Frame:
        result = frame
        for node in self.nodes:
            if not node.enabled:
                continue
            effect = self._instances.setdefault(
                node.node_id, self.registry.create(node.type_name)
            )
            # Cache validated params to avoid re-validation every frame
            params_hash = hash(frozenset(node.params.items()))
            if params_hash != node._cached_params_hash:
                node._cached_params = effect.parameters.validate(node.params)
                node._cached_params_hash = params_hash
            assert node._cached_params is not None
            result = effect.apply(result, node._cached_params, context)
        return result

    def add(self, type_name: str, params: dict[str, object] | None = None) -> EffectNode:
        node = EffectNode(type_name=type_name, params=params or {})
        self.nodes.append(node)
        self._instances[node.node_id] = self.registry.create(type_name)
        return node

    def remove(self, index: int) -> EffectNode:
        node = self.nodes.pop(index)
        self._instances.pop(node.node_id, None)
        return node

    def move(self, old_index: int, new_index: int) -> None:
        node = self.nodes.pop(old_index)
        self.nodes.insert(new_index, node)

    def duplicate(self, index: int) -> EffectNode:
        node = self.nodes[index].duplicate()
        self.nodes.insert(index + 1, node)
        self._instances[node.node_id] = self.registry.create(node.type_name)
        return node

    def to_config(self) -> list[dict[str, object]]:
        return [
            {
                "type": node.type_name,
                "node_id": node.node_id,
                "label": node.label,
                "enabled": node.enabled,
                "params": dict(node.params),
            }
            for node in self.nodes
        ]
