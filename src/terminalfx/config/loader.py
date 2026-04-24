from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

import yaml

from terminalfx.config.schema import (
    AudioConfig,
    OutputConfig,
    PreviewConfig,
    ProjectConfig,
    SourceConfig,
)
from terminalfx.core.errors import ConfigError
from terminalfx.core.types import PreviewMode, RenderMode, Resolution, SourceKind


def load_project(path: str | Path) -> ProjectConfig:
    config_path = Path(path)
    try:
        payload = yaml.safe_load(config_path.read_text()) or {}
    except OSError as error:
        raise ConfigError(f"unable to read config: {config_path}") from error
    except yaml.YAMLError as error:
        raise ConfigError(f"invalid YAML in config: {config_path}") from error

    base = config_path.parent
    project = ProjectConfig(
        schema_version=int(payload.get("schema_version", 1)),
        project_name=str(payload.get("project_name", "terminalfx")),
        resolution=_resolution(payload.get("resolution", {})),
        source=_source(payload.get("source", {}), base),
        preview=_preview(payload.get("preview", {}), base),
        output=_output(payload.get("output", {}), base),
        audio=_audio(payload.get("audio", {})),
        effects=list(payload.get("effects", [])),
    )
    try:
        project.validate()
    except ValueError as error:
        raise ConfigError(str(error)) from error
    return project


def save_project(config: ProjectConfig, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(to_plain_data(config), sort_keys=False))
    return output_path


def to_plain_data(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, StrEnum):
        return str(value)
    if is_dataclass(value):
        return {key: to_plain_data(item) for key, item in asdict(cast(Any, value)).items()}
    if isinstance(value, dict):
        return {str(key): to_plain_data(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [to_plain_data(item) for item in value]
    return value


def _resolution(payload: dict[str, Any]) -> Resolution:
    return Resolution(
        width=int(payload.get("width", 1920)),
        height=int(payload.get("height", 1080)),
        fps=int(payload.get("fps", 60)),
    )


def _source(payload: dict[str, Any], base: Path) -> SourceConfig:
    path = payload.get("path")
    source_path = _resolve_path(base, path) if path else None
    return SourceConfig(
        kind=SourceKind(str(payload.get("kind", payload.get("mode", SourceKind.MOCK)))),
        path=source_path,
        camera_index=int(payload.get("camera_index", 0)),
        screen_index=int(payload.get("screen_index", 0)),
        window_title=payload.get("window_title", payload.get("window_name")),
        loop=bool(payload.get("loop", True)),
    )


def _preview(payload: dict[str, Any], base: Path) -> PreviewConfig:
    transport_path = _resolve_path(base, payload.get("transport_path", "run/preview-state.json"))
    return PreviewConfig(
        enabled=bool(payload.get("enabled", True)),
        mode=PreviewMode(str(payload.get("mode", PreviewMode.AUTO))),
        display_index=int(payload.get("display_index", 1)),
        fullscreen=bool(payload.get("fullscreen", True)),
        refresh_hz=int(payload.get("refresh_hz", 60)),
        character_width=int(payload.get("character_width", 160)),
        character_height=int(payload.get("character_height", 90)),
        transport_path=transport_path,
    )


def _output(payload: dict[str, Any], base: Path) -> OutputConfig:
    directory = _resolve_path(base, payload.get("directory", "output"))
    return OutputConfig(
        directory=directory,
        video_path=_resolve_path(base, payload.get("video_path", directory / "render.mp4")),
        image_path=_resolve_path(base, payload.get("image_path", directory / "frame.png")),
        codec=str(payload.get("codec", "mp4v")),
        render_mode=RenderMode(str(payload.get("render_mode", RenderMode.OFFLINE))),
    )


def _audio(payload: dict[str, Any]) -> AudioConfig:
    return AudioConfig(
        enabled=bool(payload.get("enabled", True)),
        waveform_resolution=int(payload.get("waveform_resolution", 128)),
        analysis_window_seconds=float(payload.get("analysis_window_seconds", 1.0)),
    )


def _resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()
