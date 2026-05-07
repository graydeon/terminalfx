from __future__ import annotations

from pathlib import Path
from time import monotonic
from typing import cast

import cv2

from terminalfx.config import load_project
from terminalfx.core.types import Frame, FramePacket, PreviewMode, TransportStatus
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
        # snapshot change detection
        self._last_snapshot_timestamp: float = 0.0
        self._cached_status: TransportStatus = TransportStatus.STOPPED
        self._cached_mode: PreviewMode = self.project.preview.mode
        self._cached_hud_lines: list[str] = []
        # pipeline change detection — cached at apply time
        self._effects_changed = True

    def run(self) -> None:
        self._open_window()
        frame_count = 0
        last_status_at = monotonic()
        last_fps_update_at = monotonic()
        status_interval = 0.5
        fps_frame_count = 0
        fps_actual = 0.0
        # Per-phase timing accumulators (ms)
        t_read = t_apply = t_pipe = t_render = t_show = 0.0
        try:
            self.transport.send_status(
                {"preview_ready": True, "status": "starting"}
            )
            while True:
                t0 = monotonic()

                t1 = monotonic()
                snapshot = self.transport.read_state()
                t_read = monotonic() - t1
                if snapshot and snapshot.get("stop_requested"):
                    self.transport.send_status(
                        {"preview_ready": False, "status": "stopped"}
                    )
                    break

                t1 = monotonic()
                self._apply_snapshot_if_changed(snapshot)
                pipeline = self._pipeline_for_project()
                t_apply = monotonic() - t1

                status = self._cached_status
                if status == TransportStatus.PAUSED:
                    frame = self.renderer.waiting_frame(
                        self.project.resolution.width,
                        self.project.resolution.height,
                        ["paused", f"source: {self.project.source.kind}"],
                    )
                else:
                    t1 = monotonic()
                    packet = pipeline.render_next(self._cached_mode)
                    t_pipe = monotonic() - t1
                    if packet is None:
                        frame = self.renderer.waiting_frame(
                            self.project.resolution.width,
                            self.project.resolution.height,
                            ["source produced no frame",
                             f"source: {self.project.source.kind}"],
                        )
                    else:
                        t1 = monotonic()
                        frame = self._render_packet(packet, snapshot, status)
                        t_render = monotonic() - t1

                t1 = monotonic()
                cv2.imshow(self.window_name, frame)
                t_show = monotonic() - t1

                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    self.transport.send_status(
                        {"preview_ready": False, "status": "closed"}
                    )
                    break

                frame_count += 1
                fps_frame_count += 1
                now = monotonic()
                frame_ms = (now - t0) * 1000.0
                if now - last_fps_update_at >= 1.0:
                    fps_actual = fps_frame_count / max(0.001, now - last_fps_update_at)
                    fps_frame_count = 0
                    last_fps_update_at = now
                if now - last_status_at >= status_interval:
                    self.transport.send_status({
                        "preview_ready": True,
                        "status": "running",
                        "frame_count": frame_count,
                        "fps_actual": round(fps_actual, 1),
                        "source_name": self.project.source.kind.name,
                        "frame_ms": round(frame_ms, 1),
                        "read_ms": round(t_read * 1000, 1),
                        "snap_ms": round(t_apply * 1000, 1),
                        "pipe_ms": round(t_pipe * 1000, 1),
                        "rend_ms": round(t_render * 1000, 1),
                        "show_ms": round(t_show * 1000, 1),
                    })
                    last_status_at = now
        except Exception as exc:
            self.transport.send_status(
                {"preview_ready": False, "status": "error", "error": str(exc)}
            )
        finally:
            self._close_pipeline()
            cv2.destroyWindow(self.window_name)

    def _open_window(self) -> None:
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        monitors = list_monitors()
        if monitors:
            monitor = monitors[self.project.preview.display_index % len(monitors)]
            cv2.moveWindow(self.window_name, monitor.x, monitor.y)
        # Size window to project resolution, not monitor — avoids GPU upscale cost
        cv2.resizeWindow(
            self.window_name,
            self.project.resolution.width,
            self.project.resolution.height,
        )
        if self.project.preview.fullscreen:
            cv2.setWindowProperty(
                self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
            )

    def _render_packet(
        self,
        packet: FramePacket,
        snapshot: dict[str, object] | None,
        status: TransportStatus,
    ) -> Frame:
        """Render a single frame packet with HUD overlay."""
        source_is_live = self.project.source.kind.value in {"camera", "screen", "window"}
        return self.renderer.render(
            packet.frame,
            self._cached_mode,
            self._cached_hud_lines,
            source_is_live=source_is_live,
        )

    def _apply_snapshot_if_changed(self, snapshot: dict[str, object] | None) -> None:
        """Apply snapshot config changes only when the snapshot actually changed."""
        if snapshot is None:
            return
        ts = snapshot.get("timestamp")
        if isinstance(ts, (int, float)) and ts == self._last_snapshot_timestamp:
            return  # no change — skip expensive dict lookups
        if isinstance(ts, (int, float)):
            self._last_snapshot_timestamp = float(ts)
        self._apply_snapshot(snapshot)

    def _apply_snapshot(self, snapshot: dict[str, object]) -> None:
        preview_mode = snapshot.get("preview_mode")
        if preview_mode is not None:
            self._cached_mode = PreviewMode(str(preview_mode))
            self.project.preview.mode = self._cached_mode

        effects = snapshot.get("effects")
        if isinstance(effects, list):
            self.project.effects = cast(list[dict[str, object]], effects)
            self._effects_changed = True

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

        status_str = snapshot.get("transport_status", "STOPPED")
        self._cached_status = TransportStatus(str(status_str))

        name = str(snapshot.get("project_name", self.project.project_name))
        src_name = self.project.source.kind.name
        self._cached_hud_lines = [
            f"terminalfx | {name}",
            f"source: {src_name}",
            f"mode: {self._cached_mode}",
            f"status: {self._cached_status}",
        ]

    def _pipeline_for_project(self) -> RenderPipeline:
        key = (
            str(self.project.source.kind),
            str(self.project.source.path) if self.project.source.path else None,
            self.project.source.camera_index,
            self.project.source.screen_index,
            self.project.source.window_title,
        )
        if self._pipeline is not None and key == self._source_key:
            if self._effects_changed:
                self._pipeline.effect_stack = EffectStack.from_config(self.project.effects)
                self._effects_changed = False
            return self._pipeline
        self._close_pipeline()
        source = create_source(self.project.source, self.project.resolution)
        source.open()
        self._pipeline = RenderPipeline(
            source, EffectStack.from_config(self.project.effects), self.project
        )
        self._source_key = key
        self._effects_changed = False
        return self._pipeline

    def _close_pipeline(self) -> None:
        if self._pipeline is not None:
            self._pipeline.source.close()
        self._pipeline = None
        self._source_key = None


def run_preview_window(config_path: Path) -> None:
    PreviewWindow(config_path).run()
