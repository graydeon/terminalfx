from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Label, RichLog, Static

from terminalfx.config import load_project
from terminalfx.core.types import TransportStatus
from terminalfx.effects.stack import EffectNode
from terminalfx.preview.controller import PreviewProcessController
from terminalfx.preview.transport import JsonPreviewTransport
from terminalfx.session import commands as cmd
from terminalfx.session.controller import SessionController
from terminalfx.session.model import SessionState
from terminalfx.sources.screen import list_window_titles


class TextPanel(Static):
    def __init__(
        self,
        content: str = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            content,
            expand=expand,
            shrink=shrink,
            markup=False,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )

    def set(self, value: str) -> None:
        self.update(value)


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

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("o", "open_preview", "Preview"),
        Binding("m", "cycle_source", "Source"),
        Binding("c", "cycle_camera", "Camera"),
        Binding("S", "cycle_screen", "Screen"),
        Binding("w", "cycle_window", "Window"),
        Binding("p", "cycle_preview", "Mode"),
        Binding("space", "toggle_play", "Play"),
        Binding("r", "toggle_record", "Record"),
        Binding("e", "queue_export", "Export"),
        Binding("j", "select_down", "Down"),
        Binding("k", "select_up", "Up"),
        Binding("J", "move_down", "MoveDn"),
        Binding("K", "move_up", "MoveUp"),
        Binding("a", "add_effect", "Add"),
        Binding("x", "remove_effect", "Remove"),
        Binding("b", "toggle_bypass", "Bypass"),
        Binding("d", "duplicate_effect", "Duplicate"),
        Binding("n", "next_look_control", "NextLook"),
        Binding("N", "previous_look_control", "PrevLook"),
        Binding("[", "decrease_look_control", "Look-"),
        Binding("]", "increase_look_control", "Look+"),
        Binding("s", "save_preset", "SavePreset"),
        Binding("l", "load_preset", "LoadPreset"),
    ]

    def __init__(self, config_path: Path) -> None:
        super().__init__()
        self.config_path = config_path.resolve()
        project = load_project(self.config_path)
        self.controller = SessionController(SessionState.from_project(project))
        self.transport = JsonPreviewTransport(project.preview.transport_path)
        self.preview_log_path = project.preview.transport_path.parent / "preview-window.log"
        self.preview_process = PreviewProcessController(self.config_path, self.preview_log_path)
        self.look_control_index = 0
        self.source_panel: TextPanel
        self.preview_panel: TextPanel
        self.transport_panel: TextPanel
        self.effects_table: DataTable[str]
        self.params_panel: TextPanel
        self.export_panel: TextPanel
        self.audio_panel: TextPanel
        self.log_panel: RichLog
        self.keys_panel: TextPanel

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
        self.controller.subscribe(lambda state: self.transport.send_state(state))
        self.refresh_view("control surface ready")

    def refresh_view(self, log_message: str | None = None) -> None:
        state = self.controller.state
        self.transport.send_state(state)
        self._source(state)
        self._preview(state)
        self._transport(state)
        self._effects(state)
        self._params(state)
        self._export(state)
        self._audio(state)
        self.keys_panel.set(
            "o preview\nm source\nc camera\nS screen\nw window\np mode\n"
            "space play\nr record\ne export\nj/k select\nJ/K move\n"
            "a add\nx remove\nb bypass\nd duplicate\nn/N look slider\n"
            "[ and ] adjust look\ns save preset\nl load preset"
        )
        if log_message:
            state.append_log(log_message)
        for line in state.log[-3:]:
            self.log_panel.write(line)

    def _source(self, state: SessionState) -> None:
        source = state.project.source
        self.source_panel.set(
            f"kind: {source.kind}\npath: {source.path or '-'}\ncamera: {source.camera_index}\n"
            f"screen: {source.screen_index}\nwindow: {source.window_title or '-'}"
        )

    def _preview(self, state: SessionState) -> None:
        preview = state.project.preview
        self.preview_panel.set(
            f"mode: {state.preview_mode}\ndisplay: {preview.display_index}\n"
            f"fullscreen: {preview.fullscreen}\nrefresh: {preview.refresh_hz} hz\n"
            f"density: {preview.character_width}x{preview.character_height}\n"
            f"transport: {preview.transport_path}"
        )

    def _transport(self, state: SessionState) -> None:
        self.transport_panel.set(
            f"status: {state.transport_status}\nrecord armed: {state.recording_armed}\n"
            f"playhead: {state.playhead_seconds:.2f}s"
        )

    def _effects(self, state: SessionState) -> None:
        self.effects_table.clear(columns=False)
        for index, node in enumerate(state.effect_stack.nodes):
            marker = ">" if index == state.selected_effect_index else " "
            enabled = "on" if node.enabled else "byp"
            self.effects_table.add_row(
                f"{marker}{index}", node.type_name, enabled, str(node.params)
            )

    def _params(self, state: SessionState) -> None:
        node = state.selected_effect
        if node is None:
            self.params_panel.set("no effect selected")
            return
        effect = state.effect_stack.registry.create(node.type_name)
        params = effect.parameters.validate(node.params)
        lines = [
            "look sliders:",
            *self._look_slider_lines(state),
            "",
            f"{effect.display_name}",
            f"type: {node.type_name}",
            "params:",
        ]
        lines.extend(f"  {key}: {value}" for key, value in params.items())
        self.params_panel.set("\n".join(lines))

    def _export(self, state: SessionState) -> None:
        output = state.project.output
        queue = (
            "\n".join(f"  {job.kind}: {job.status}" for job in state.export_queue[-5:]) or "  idle"
        )
        self.export_panel.set(
            f"video: {output.video_path}\n"
            f"image: {output.image_path}\n"
            f"mode: {output.render_mode}\n"
            f"queue:\n{queue}"
        )

    def _audio(self, state: SessionState) -> None:
        audio = state.project.audio
        self.audio_panel.set(
            f"enabled: {audio.enabled}\nwaveform points: {audio.waveform_resolution}\n"
            f"window: {audio.analysis_window_seconds:.2f}s\nstatus: silent analyzer"
        )

    def action_open_preview(self) -> None:
        self.preview_process.start()
        self.refresh_view(f"preview launched | log: {self.preview_log_path}")

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
        self.controller.state.project.source.window_title = titles[(index + 1) % len(titles)]
        self.controller.state.append_log(
            f"window target: {self.controller.state.project.source.window_title}"
        )
        self.refresh_view()

    def action_cycle_preview(self) -> None:
        self.controller.cycle_preview_mode()
        self.refresh_view()

    def action_next_look_control(self) -> None:
        controls = self._look_controls(self.controller.state)
        self.look_control_index = (self.look_control_index + 1) % len(controls)
        self.refresh_view()

    def action_previous_look_control(self) -> None:
        controls = self._look_controls(self.controller.state)
        self.look_control_index = (self.look_control_index - 1) % len(controls)
        self.refresh_view()

    def action_increase_look_control(self) -> None:
        self._adjust_look_control(1)
        self.refresh_view()

    def action_decrease_look_control(self) -> None:
        self._adjust_look_control(-1)
        self.refresh_view()

    def action_toggle_play(self) -> None:
        self.controller.toggle_play()
        self.refresh_view()

    def action_toggle_record(self) -> None:
        self.controller.toggle_record_arm()
        if self.controller.state.recording_armed:
            self.controller.dispatch(cmd.SetTransport(TransportStatus.RECORDING))
        self.refresh_view()

    def action_queue_export(self) -> None:
        self.controller.dispatch(cmd.QueueExport("png"))
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
        self.controller.dispatch(cmd.AddEffect("phosphor_trail"))
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
        path = self.config_path.parent / "presets" / "selected-effect.yaml"
        self.controller.dispatch(cmd.SaveSelectedEffectPreset(path))
        self.refresh_view()

    def action_load_preset(self) -> None:
        path = self.config_path.parent / "presets" / "selected-effect.yaml"
        if not path.exists():
            self.controller.state.append_log(f"preset not found: {path}")
            self.refresh_view()
            return
        self.controller.dispatch(cmd.LoadEffectPreset(path))
        self.refresh_view()

    def _look_slider_lines(self, state: SessionState) -> list[str]:
        controls = self._look_controls(state)
        self.look_control_index %= len(controls)
        return [
            self._slider_line(index, label, value, minimum, maximum)
            for index, (label, value, minimum, maximum, _step) in enumerate(controls)
        ]

    def _slider_line(
        self, index: int, label: str, value: float, minimum: float, maximum: float
    ) -> str:
        width = 18
        normalized = 0.0 if maximum == minimum else (value - minimum) / (maximum - minimum)
        marker = max(0, min(width - 1, round(normalized * (width - 1))))
        cells = ["-"] * width
        cells[marker] = "|"
        prefix = ">" if index == self.look_control_index else " "
        return f"{prefix} {label:<10} [{''.join(cells)}] {value:g}"

    def _look_controls(self, state: SessionState) -> list[tuple[str, float, float, float, float]]:
        ascii_node = self._first_effect_node(state, "ascii_quantize")
        tint_node = self._first_effect_node(state, "terminal_tint")
        preview = state.project.preview
        return [
            ("density", float(preview.character_width), 80.0, 320.0, 8.0),
            ("contrast", self._param(ascii_node, "contrast", 1.15), 0.2, 3.0, 0.05),
            ("brightness", self._param(ascii_node, "brightness", 0.0), -80.0, 80.0, 2.0),
            ("levels", self._param(ascii_node, "levels", 9.0), 2.0, 24.0, 1.0),
            ("tint", self._param(tint_node, "intensity", 0.85), 0.0, 1.0, 0.05),
        ]

    def _adjust_look_control(self, direction: int) -> None:
        state = self.controller.state
        controls = self._look_controls(state)
        self.look_control_index %= len(controls)
        label, value, minimum, maximum, step = controls[self.look_control_index]
        next_value = max(minimum, min(maximum, value + step * direction))
        if label == "density":
            width = int(round(next_value / 8.0) * 8)
            state.project.preview.character_width = width
            state.project.preview.character_height = max(1, round(width * 9 / 16))
            state.append_log(
                "density: "
                f"{state.project.preview.character_width}x{state.project.preview.character_height}"
            )
            return
        if label in {"contrast", "brightness", "levels"}:
            node = self._first_effect_node(state, "ascii_quantize")
            if node is not None:
                node.params[label] = int(next_value) if label == "levels" else round(next_value, 2)
                state.append_log(f"{label}: {node.params[label]}")
            return
        if label == "tint":
            node = self._first_effect_node(state, "terminal_tint")
            if node is not None:
                node.params["intensity"] = round(next_value, 2)
                state.append_log(f"tint intensity: {node.params['intensity']}")

    def _first_effect_node(self, state: SessionState, type_name: str) -> EffectNode | None:
        for node in state.effect_stack.nodes:
            if node.type_name == type_name:
                return node
        return None

    def _param(self, node: EffectNode | None, name: str, default: float) -> float:
        if node is None:
            return default
        value = node.params.get(name, default)
        return float(cast(Any, value))
