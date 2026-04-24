from pathlib import Path

from terminalfx.config import load_project
from terminalfx.core.types import SourceKind


def test_default_config_loads_with_mock_source() -> None:
    project = load_project(Path("examples/configs/default.yaml"))

    assert project.project_name == "terminalfx"
    assert project.source.kind == SourceKind.MOCK
    assert project.source.path is None
    assert project.preview.transport_path.name == "preview-state.json"
    assert len(project.effects) == 3


def test_relative_paths_resolve_from_config_location() -> None:
    project = load_project(Path("examples/configs/default.yaml"))

    assert project.output.image_path.is_absolute()
    assert project.output.image_path.parent.name == "output"
