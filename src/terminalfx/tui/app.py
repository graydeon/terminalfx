from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Label, RichLog

from terminalfx.config import load_project
from terminalfx.core.types import TransportStatus
from terminalfx.preview.controller import PreviewProcessController
from terminalfx.preview.transport import JsonPreviewTransport
from terminalfx.session import commands as cmd
from terminalfx.session.controller import SessionController
from terminalfx.session.model import SessionState
from terminalfx.sources.screen import list_window_titles
from terminalfx.tui.bindings import BINDINGS as _BINDINGS
from terminalfx.tui.bindings import KEYS_HELP
from terminalfx.tui.export_worker import ExportWorker
from terminalfx.tui.look_controls import (
    adjust_look_control,
    build_look_controls,
    render_slider_lines,
)
from terminalfx.tui.panels import (
    refresh_audio_panel,
    refresh_effects_table,
    refresh_export_panel,
    refresh_params_panel,
    refresh_source_panel,
    refresh_transport_panel,
)
from terminalfx.tui.widgets import TextPanel


class TerminalFxApp(App[None]):
    CSS = """
    Screen { background: black; color: white; layout: vertical; }
    Header, Footer { background: black; color: white; }
    #body { height: 1fr; }
    .column { height: 1fr; border: solid white; padding: 0 1; }
    #left { width: 30; }
    #center { width: 1fr; }
    #right { width: 40; }
    .panel-title { text-style: bold; margin: 1 0 0 0; }
    .box { border: solid white; padding: 0 1; margin: 0 0 1 0; }
    DataTable { height: 15; margin: 0 0 1 0; }
    RichLog { height: 12; border: solid white; }
    """

    BINDINGS = _BINDINGS  # type: ignore[assignment]

    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.config_path = config_path.resolve()
        project = load_project(self.config_path)
        self.controller = SessionController(SessionState.from_project(project))
        self.transport = JsonPreviewTransport(project.preview.transport_path)
        self.preview_log_path = (
            project.preview.transport_path.parent / "preview-window.log"
        )
        self.preview_process = PreviewProcessController(
            self.config_path, self.preview_log_path
        )
        self.look_control_index = 0
        self._effect_add_index = 0
        self._export_worker = ExportWorker(
            lambda: self.call_from_thread(self.refresh_view),
            lambda: self.controller.state,
        )
        self.source_panel: TextPanel
        self.preview_panel: TextPanel
        self.transport_panel: TextPanel
        self.effects_table: DataTable[str]
        self.params_panel: TextPanel
        self.export_panel: TextPanel
        self.audio_panel: TextPanel
        self.log_panel: RichLog
        self.keys_panel: TextPanel

    # ── composition ──────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="body"):
            with Vertical(id="left", classes="column"):
                yield Label("SOURCE", classes="panel-title")
                self.source_panel = TextPanel(classes="box")
                yield self.source_panel
                yield Label("PREVIEW", classes="panel-title")
                self.preview_panel = TextPanel(classes="box")
                yield self.preview_panel
                yield Label("TRANSPORT", classes="panel-title")
                self.transport_panel = TextPanel(classes="box")
                yield self.transport_panel
            with Vertical(id="center", classes="column"):
                yield Label("EFFECT STACK", classes="panel-title")
                self.effects_table = DataTable(zebra_stripes=True)
                yield self.effects_table
                yield Label("PARAMETERS", classes="panel-title")
                self.params_panel = TextPanel(classes="box")
                yield self.params_panel
            with Vertical(id="right", classes="column"):
                yield Label("EXPORT", classes="panel-title")
                self.export_panel = TextPanel(classes="box")
                yield self.export_panel
                yield Label("AUDIO", classes="panel-title")
                self.audio_panel = TextPanel(classes="box")
                yield self.audio_panel
                yield Label("LOG", classes="panel-title")
                self.log_panel = RichLog(markup=False)
                yield self.log_panel
                yield Label("KEYS", classes="panel-title")
                self.keys_panel = TextPanel(classes="box")
                yield self.keys_panel
        yield Footer()

    def on_mount(self) -> None:
        self.effects_table.add_columns("#", "effect", "state", "params")
        self.controller.subscribe(
            lambda state: self.transport.send_state(state)
        )
        self._export_worker.start()
        self.set_interval(1.0, self._poll_preview_status)
        self.refresh_view("control surface ready")

    def _poll_preview_status(self) -> None:
        status = self.transport.read_status()
        if status is None:
            return
        state = self.controller.state
        preview = state.project.preview
        status_text = status.get("status", "unknown")
        preview_ready = status.get("preview_ready", False)
        lines = [
            f"mode: {state.preview_mode}",
            f"display: {preview.display_index}",
            f"fullscreen: {preview.fullscreen}",
            f"refresh: {preview.refresh_hz} hz",
            f"density: {preview.character_width}x{preview.character_height}",
            f"transport: {preview.transport_path}",
        ]
        if preview_ready:
            lines.append(f"preview: {status_text}")
            if status.get("fps_actual"):
                lines.append(f"fps: {status['fps_actual']}")
            if status.get("frame_ms"):
                lines.append(f"frame: {status['frame_ms']}ms")
                lines.append(
                    f"  read={status.get('read_ms','?')}ms"
                    f" snap={status.get('snap_ms','?')}ms"
                    f" pipe={status.get('pipe_ms','?')}ms"
                )
                lines.append(
                    f"  rend={status.get('rend_ms','?')}ms"
                    f" show={status.get('show_ms','?')}ms"
                )
            if status.get("source_name"):
                lines.append(f"src: {status['source_name']}")
            if status.get("frame_count"):
                lines.append(f"frames: {status['frame_count']}")
        elif status_text == "error":
            lines.append(f"error: {status.get('error', '?')}")
        self.preview_panel.set("\n".join(lines))

    # ── unified refresh ──────────────────────────────────────────────

    def refresh_view(self, log_message: str | None = None) -> None:
        state = self.controller.state
        self.transport.send_state(state)
        refresh_source_panel(self.source_panel, state)
        refresh_transport_panel(self.transport_panel, state)
        refresh_effects_table(self.effects_table, state)
        refresh_params_panel(
            self.params_panel,
            state,
            render_slider_lines(
                build_look_controls(state), self.look_control_index
            ),
        )
        refresh_export_panel(self.export_panel, state)
        refresh_audio_panel(self.audio_panel, state)
        self.keys_panel.set(KEYS_HELP)
        if log_message:
            state.append_log(log_message)
        for line in state.log[-3:]:
            self.log_panel.write(line)

    # ── action dispatch ──────────────────────────────────────────────

    def action_open_preview(self) -> None:
        self.preview_process.start()
        self.refresh_view(f"preview launched | log: {self.preview_log_path}")

    def action_close_preview(self) -> None:
        self.preview_process.request_stop(self.transport)
        self.refresh_view("preview stopped")

    def action_cycle_source(self) -> None:
        self.controller.cycle_source_kind()
        self.refresh_view()

    def action_cycle_camera(self) -> None:
        source = self.controller.state.project.source
        source.camera_index = (source.camera_index + 1) % 8
        self.controller.state.append_log(f"camera index: {source.camera_index}")
        self.refresh_view()

    def action_cycle_screen(self) -> None:
        source = self.controller.state.project.source
        source.screen_index = (source.screen_index + 1) % 8
        self.controller.state.append_log(f"screen index: {source.screen_index}")
        self.refresh_view()

    def action_cycle_window(self) -> None:
        titles = list_window_titles()
        if not titles:
            self.controller.state.append_log("no windows discovered")
            self.refresh_view()
            return
        current = self.controller.state.project.source.window_title
        index = titles.index(current) if current in titles else -1
        self.controller.state.project.source.window_title = titles[
            (index + 1) % len(titles)
        ]
        self.controller.state.append_log(
            f"window target: {self.controller.state.project.source.window_title}"
        )
        self.refresh_view()

    def action_cycle_preview(self) -> None:
        self.controller.cycle_preview_mode()
        self.refresh_view()

    def action_next_look_control(self) -> None:
        controls = build_look_controls(self.controller.state)
        self.look_control_index = (self.look_control_index + 1) % len(controls)
        self.refresh_view()

    def action_previous_look_control(self) -> None:
        controls = build_look_controls(self.controller.state)
        self.look_control_index = (self.look_control_index - 1) % len(controls)
        self.refresh_view()

    def action_increase_look_control(self) -> None:
        adjust_look_control(self.controller.state, 1, self.look_control_index)
        self.refresh_view()

    def action_decrease_look_control(self) -> None:
        adjust_look_control(self.controller.state, -1, self.look_control_index)
        self.refresh_view()

    def action_toggle_play(self) -> None:
        self.controller.toggle_play()
        self.refresh_view()

    def action_toggle_record(self) -> None:
        self.controller.toggle_record_arm()
        if self.controller.state.recording_armed:
            self.controller.dispatch(cmd.SetTransport(TransportStatus.RECORDING))
        self.refresh_view()

    def action_queue_export_png(self) -> None:
        self.controller.dispatch(cmd.QueueExport("png"))
        self.refresh_view()

    def action_queue_export_mp4(self) -> None:
        self.controller.dispatch(cmd.QueueExport("mp4"))
        self.refresh_view()

    def action_select_down(self) -> None:
        self.controller.dispatch(cmd.SelectEffect(1))
        self.refresh_view()

    def action_select_up(self) -> None:
        self.controller.dispatch(cmd.SelectEffect(-1))
        self.refresh_view()

    def action_move_down(self) -> None:
        self.controller.dispatch(cmd.MoveSelectedEffect(1))
        self.refresh_view()

    def action_move_up(self) -> None:
        self.controller.dispatch(cmd.MoveSelectedEffect(-1))
        self.refresh_view()

    def action_add_effect(self) -> None:
        names = self.controller.state.effect_stack.registry.names()
        if not names:
            return
        name = names[self._effect_add_index % len(names)]
        self._effect_add_index += 1
        self.controller.dispatch(cmd.AddEffect(name))
        self.refresh_view()

    def action_remove_effect(self) -> None:
        self.controller.dispatch(cmd.RemoveSelectedEffect())
        self.refresh_view()

    def action_toggle_bypass(self) -> None:
        self.controller.dispatch(cmd.ToggleSelectedEffect())
        self.refresh_view()

    def action_duplicate_effect(self) -> None:
        self.controller.dispatch(cmd.DuplicateSelectedEffect())
        self.refresh_view()

    def action_save_preset(self) -> None:
        node = self.controller.state.selected_effect
        if node is None:
            self.controller.state.append_log("no effect selected to save")
            self.refresh_view()
            return
        path = self.config_path.parent / "presets" / f"{node.type_name}.yaml"
        self.controller.dispatch(cmd.SaveSelectedEffectPreset(path))
        self.refresh_view()

    def action_load_preset(self) -> None:
        node = self.controller.state.selected_effect
        if node is None:
            self.controller.state.append_log("no effect selected to load into")
            self.refresh_view()
            return
        path = self.config_path.parent / "presets" / f"{node.type_name}.yaml"
        if not path.exists():
            self.controller.state.append_log(f"preset not found: {path}")
            self.refresh_view()
            return
        self.controller.dispatch(cmd.LoadEffectPreset(path))
        self.refresh_view()
