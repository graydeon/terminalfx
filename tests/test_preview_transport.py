from pathlib import Path

from terminalfx.config.schema import ProjectConfig
from terminalfx.preview.transport import JsonPreviewTransport
from terminalfx.session.model import SessionState


def test_json_preview_transport_writes_snapshot(tmp_path: Path) -> None:
    transport = JsonPreviewTransport(tmp_path / "preview.json")

    transport.send_state(SessionState.from_project(ProjectConfig()))
    payload = transport.read_state()

    assert payload is not None
    assert payload["project_name"] == "terminalfx"
    assert payload["preview_mode"] == "auto"
    assert payload["effects"]
