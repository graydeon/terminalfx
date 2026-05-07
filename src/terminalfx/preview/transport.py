from __future__ import annotations

import json
import os
import time as _time
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

    def send_status(self, status: dict[str, Any]) -> None:
        """Send status from preview back to TUI."""

    def read_status(self) -> dict[str, Any] | None:
        """Read the latest preview status."""


class JsonPreviewTransport:
    """Local transport with atomic writes — bidirectional.

    TUI -> preview:  send_state() writes to path (preview-state.json)
    preview -> TUI:  send_status() writes to status_path (preview-status.json)

    Performance: read_state() caches the last mtime and only re-reads
    the file when it has actually changed on disk. This avoids JSON parse
    overhead on every preview frame.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.status_path = path.parent / "preview-status.json"
        self._last_mtime: float = 0.0
        self._last_snapshot: dict[str, Any] | None = None
        self._last_state_written: str = ""

    # ── TUI → preview ────────────────────────────────────────────────

    def send_state(self, state: SessionState) -> None:
        snapshot = PreviewSnapshot.from_session(state)
        data = json.dumps(asdict(snapshot), indent=2)
        if data == self._last_state_written:
            return  # deduplicate identical writes
        self._last_state_written = data
        self._write_json(self.path, data)

    def send_stop(self) -> None:
        snapshot = PreviewSnapshot(
            timestamp=_time.time(),
            project_name="",
            project={},
            preview_mode="",
            transport_status="STOPPED",
            selected_effect_index=0,
            effects=[],
            recording_armed=False,
            stop_requested=True,
        )
        data = json.dumps(asdict(snapshot), indent=2)
        self._last_state_written = data
        self._write_json(self.path, data)

    def read_state(self) -> dict[str, Any] | None:
        if not self.path.exists():
            self._last_mtime = 0.0
            self._last_snapshot = None
            return None
        current_mtime = self.path.stat().st_mtime
        if current_mtime == self._last_mtime and self._last_snapshot is not None:
            return self._last_snapshot
        self._last_mtime = current_mtime
        self._last_snapshot = self._read_json(self.path)
        return self._last_snapshot

    # ── preview → TUI ────────────────────────────────────────────────

    def send_status(self, status: dict[str, Any]) -> None:
        payload: dict[str, Any] = {"timestamp": _time.time(), **status}
        self._write_json(self.status_path, json.dumps(payload, indent=2))

    def read_status(self) -> dict[str, Any] | None:
        return self._read_json(self.status_path)

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _write_json(path: Path, data: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(data)
        os.replace(tmp_path, path)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
