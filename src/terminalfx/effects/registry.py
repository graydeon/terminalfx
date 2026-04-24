from __future__ import annotations

from dataclasses import dataclass, field

from terminalfx.core.errors import EffectError
from terminalfx.effects.base import Effect
from terminalfx.effects.builtins import (
    AsciiQuantizeEffect,
    PassthroughEffect,
    PhosphorTrailEffect,
    TerminalTintEffect,
)


@dataclass(slots=True)
class EffectRegistry:
    _factories: dict[str, type[Effect]] = field(default_factory=dict)

    def register(self, factory: type[Effect]) -> None:
        self._factories[factory.type_name] = factory

    def create(self, type_name: str) -> Effect:
        try:
            return self._factories[type_name]()
        except KeyError as error:
            raise EffectError(f"unknown effect type: {type_name}") from error

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))


def default_effect_registry() -> EffectRegistry:
    registry = EffectRegistry()
    registry.register(PassthroughEffect)
    registry.register(AsciiQuantizeEffect)
    registry.register(TerminalTintEffect)
    registry.register(PhosphorTrailEffect)
    return registry
