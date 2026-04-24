from __future__ import annotations

import json
from pathlib import Path
from time import sleep
from typing import cast

import cv2

from terminalfx.config import load_project
from terminalfx.core.types import Frame, PreviewMode, TransportStatus
from terminalfx.effects.stack import EffectStack
from terminalfx.preview.renderer import PreviewRenderer
from terminalfx.preview.transport import JsonPreviewTransport
from terminalfx.render.pipeline import RenderPipeline
from terminalfx.sources import create_source
from terminalfx.sources.screen import list_monitors


class PreviewWindow:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.project = load_project(config_path)
        self.transport = JsonPreviewTransport(self.project.preview.transport_path)
        self.renderer = PreviewRenderer(self.project.preview)
        self.window_name = "terminalfx-preview"
        self._pipeline: RenderPipeline | None = None
        self._source_key: tuple[str, str | None, int, int, str | None] | None = None
        self._effect_signature = ""

    def run(self) -> None:
        self._open_window()
        delay_ms = max(1, int(1000 / max(1, self.project.preview.refresh_hz)))
        try:
            while True:
                snapshot = self.transport.read_state()
                frame = self._render(snapshot)
                cv2.imshow(self.window_name, frame)
                key = cv2.waitKey(delay_ms) & 0xFF
                if key in (27, ord("q")):
                    break
                sleep(0)
        finally:
            self._close_pipeline()
            cv2.destroyWindow(self.window_name)

    def _open_window(self) -> None:
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        monitors = list_monitors()
        if monitors:
            monitor = monitors[self.project.preview.display_index % len(monitors)]
            cv2.moveWindow(self.window_name, monitor.x, monitor.y)
            cv2.resizeWindow(self.window_name, monitor.width, monitor.height)
        if self.project.preview.fullscreen:
            cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    def _render(self, snapshot: dict[str, object] | None) -> Frame:
        if snapshot is None:
            return self.renderer.waiting_frame(
                self.project.resolution.width,
                self.project.resolution.height,
                [f"waiting for {self.project.preview.transport_path}"],
            )
        self._apply_snapshot(snapshot)
        pipeline = self._pipeline_for_project()
        status = TransportStatus(str(snapshot.get("transport_status", TransportStatus.STOPPED)))
        if status == TransportStatus.PAUSED:
            return self.renderer.waiting_frame(
                self.project.resolution.width,
                self.project.resolution.height,
                ["paused", f"source: {self.project.source.kind}"],
            )
        packet = pipeline.render_next(self.project.preview.mode)
        if packet is None:
            return self.renderer.waiting_frame(
                self.project.resolution.width,
                self.project.resolution.height,
                ["source produced no frame", f"source: {self.project.source.kind}"],
            )
        return self.renderer.render(
            packet.frame,
            self.project.preview.mode,
            [
                f"terminalfx | {snapshot.get('project_name', self.project.project_name)}",
                f"source: {packet.source_name}",
                f"mode: {self.project.preview.mode}",
                f"status: {status}",
            ],
        )

    def _apply_snapshot(self, snapshot: dict[str, object]) -> None:
        preview_mode = snapshot.get("preview_mode")
        if preview_mode is not None:
            self.project.preview.mode = PreviewMode(str(preview_mode))
        effects = snapshot.get("effects")
        if isinstance(effects, list):
            self.project.effects = cast(list[dict[str, object]], effects)
        project_payload = snapshot.get("project")
        if isinstance(project_payload, dict):
            preview_payload = project_payload.get("preview")
            if isinstance(preview_payload, dict):
                width = preview_payload.get("character_width")
                height = preview_payload.get("character_height")
                if width is not None:
                    self.project.preview.character_width = int(width)
                if height is not None:
                    self.project.preview.character_height = int(height)
            source_payload = project_payload.get("source")
            if isinstance(source_payload, dict):
                kind = source_payload.get("kind")
                if kind is not None:
                    self.project.source.kind = type(self.project.source.kind)(str(kind))
                self.project.source.camera_index = int(
                    source_payload.get("camera_index", self.project.source.camera_index)
                )
                self.project.source.screen_index = int(
                    source_payload.get("screen_index", self.project.source.screen_index)
                )
                window_title = source_payload.get("window_title")
                if window_title is not None:
                    self.project.source.window_title = str(window_title)

    def _pipeline_for_project(self) -> RenderPipeline:
        key = (
            str(self.project.source.kind),
            str(self.project.source.path) if self.project.source.path else None,
            self.project.source.camera_index,
            self.project.source.screen_index,
            self.project.source.window_title,
        )
        effect_signature = json.dumps(self.project.effects, sort_keys=True)
        if self._pipeline is not None and key == self._source_key:
            if effect_signature != self._effect_signature:
                self._pipeline.effect_stack = EffectStack.from_config(self.project.effects)
                self._effect_signature = effect_signature
            return self._pipeline
        self._close_pipeline()
        source = create_source(self.project.source, self.project.resolution)
        source.open()
        self._pipeline = RenderPipeline(
            source, EffectStack.from_config(self.project.effects), self.project
        )
        self._source_key = key
        self._effect_signature = effect_signature
        return self._pipeline

    def _close_pipeline(self) -> None:
        if self._pipeline is not None:
            self._pipeline.source.close()
        self._pipeline = None
        self._source_key = None
        self._effect_signature = ""


def run_preview_window(config_path: Path) -> None:
    PreviewWindow(config_path).run()
