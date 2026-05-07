"""Tests for config validation, schema defaults, and edge cases."""

from pathlib import Path

import pytest
import yaml

from terminalfx.config import load_project
from terminalfx.config.schema import ProjectConfig
from terminalfx.core.types import SourceKind


def test_project_config_defaults_safe_no_fullscreen() -> None:
    cfg = ProjectConfig()
    assert cfg.preview.display_index == 0, "default display should be 0 (safe)"
    assert cfg.preview.fullscreen is False, "default fullscreen should be False (safe)"


def test_default_yaml_matches_schema_defaults() -> None:
    project = load_project(Path("examples/configs/default.yaml"))
    assert project.preview.display_index == 0
    assert project.preview.fullscreen is False


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    from terminalfx.core.errors import ConfigError

    bad_path = tmp_path / "bad.yaml"
    bad_path.write_text(": : : malformed: : :")
    with pytest.raises(ConfigError):
        load_project(bad_path)


def test_missing_required_fields_defaults(tmp_path: Path) -> None:
    minimal = tmp_path / "minimal.yaml"
    minimal.write_text("schema_version: 1\nproject_name: test\n")
    project = load_project(minimal)
    assert project.project_name == "test"
    assert project.source.kind == SourceKind.MOCK


def test_rejects_unsupported_schema(tmp_path: Path) -> None:
    from terminalfx.core.errors import ConfigError

    future = tmp_path / "future.yaml"
    config = {
        "schema_version": 999,
        "project_name": "future",
        "source": {"kind": "mock"},
    }
    future.write_text(yaml.dump(config))
    with pytest.raises(ConfigError, match="unsupported"):
        load_project(future)


def test_schema_version_1_validates() -> None:
    cfg = ProjectConfig(schema_version=1)
    cfg.validate()  # should not raise


def test_schema_version_0_rejected() -> None:
    cfg = ProjectConfig(schema_version=0)
    with pytest.raises(ValueError, match="unsupported"):
        cfg.validate()


def test_negative_refresh_hz_rejected() -> None:
    cfg = ProjectConfig()
    cfg.preview.refresh_hz = -1
    with pytest.raises(ValueError, match="refresh_hz"):
        cfg.validate()


def test_zero_character_dimensions_rejected() -> None:
    cfg = ProjectConfig()
    cfg.preview.character_width = 0
    with pytest.raises(ValueError, match="character"):
        cfg.validate()
