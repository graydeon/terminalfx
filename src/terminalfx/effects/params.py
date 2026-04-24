from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ParamKind = Literal["float", "int", "bool", "enum", "string"]


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    name: str
    kind: ParamKind
    default: Any
    label: str | None = None
    minimum: float | int | None = None
    maximum: float | int | None = None
    step: float | int | None = None
    options: tuple[str, ...] = ()

    def validate(self, value: Any) -> Any:
        if self.kind == "bool":
            return bool(value)
        if self.kind == "int":
            int_number = int(value)
            self._check_range(int_number)
            return int_number
        if self.kind == "float":
            float_number = float(value)
            self._check_range(float_number)
            return float_number
        if self.kind == "enum":
            text = str(value)
            if text not in self.options:
                raise ValueError(f"{self.name} must be one of {', '.join(self.options)}")
            return text
        return str(value)

    def _check_range(self, value: float | int) -> None:
        if self.minimum is not None and value < self.minimum:
            raise ValueError(f"{self.name} must be >= {self.minimum}")
        if self.maximum is not None and value > self.maximum:
            raise ValueError(f"{self.name} must be <= {self.maximum}")


@dataclass(frozen=True, slots=True)
class ParameterSchema:
    specs: tuple[ParameterSpec, ...]

    def defaults(self) -> dict[str, Any]:
        return {spec.name: spec.default for spec in self.specs}

    def validate(self, params: dict[str, Any]) -> dict[str, Any]:
        validated = self.defaults()
        by_name = {spec.name: spec for spec in self.specs}
        for key, value in params.items():
            if key not in by_name:
                raise ValueError(f"unknown parameter: {key}")
            validated[key] = by_name[key].validate(value)
        return validated

    def get(self, name: str) -> ParameterSpec:
        for spec in self.specs:
            if spec.name == name:
                return spec
        raise KeyError(name)
