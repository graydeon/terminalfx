from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol

from terminalfx.preview.messages import PreviewSnapshot
from terminalfx.session.model import SessionState


class PreviewTransport(Protocol):
    def send_state(self, state: SessionState) -> None:
        """Send a session snapshot to the preview process."""

    def read_state(self) -> dict[str, Any] | None:
        """Read the latest preview snapshot."""


class JsonPreviewTransport:
    """Simple local transport with atomic writes.

    This is intentionally a replaceable adapter. It keeps v1 easy to run while
    leaving shared memory or a socket transport free to replace it later.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def send_state(self, state: SessionState) -> None:
        snapshot = PreviewSnapshot.from_session(state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(asdict(snapshot), indent=2))
        os.replace(tmp_path, self.path)

    def read_state(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
