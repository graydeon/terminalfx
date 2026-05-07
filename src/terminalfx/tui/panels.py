"""Panel refresh methods for the terminalfx TUI.

Each _refresh_* method reads from SessionState and updates a specific
panel widget. These are pure display functions — they don't mutate state.
"""

from textual.widgets import DataTable

from terminalfx.session.model import SessionState
from terminalfx.tui.widgets import TextPanel


def refresh_source_panel(panel: TextPanel, state: SessionState) -> None:
    source = state.project.source
    panel.set(
        f"kind: {source.kind}\n"
        f"path: {source.path or '-'}\n"
        f"camera: {source.camera_index}\n"
        f"screen: {source.screen_index}\n"
        f"window: {source.window_title or '-'}"
    )


def refresh_preview_panel(panel: TextPanel, state: SessionState) -> None:
    preview = state.project.preview
    panel.set(
        f"mode: {state.preview_mode}\n"
        f"display: {preview.display_index}\n"
        f"fullscreen: {preview.fullscreen}\n"
        f"refresh: {preview.refresh_hz} hz\n"
        f"density: {preview.character_width}x{preview.character_height}\n"
        f"transport: {preview.transport_path}"
    )


def refresh_transport_panel(panel: TextPanel, state: SessionState) -> None:
    panel.set(
        f"status: {state.transport_status}\n"
        f"record armed: {state.recording_armed}\n"
        f"playhead: {state.playhead_seconds:.2f}s"
    )


def refresh_effects_table(table: DataTable[str], state: SessionState) -> None:
    table.clear(columns=False)
    for index, node in enumerate(state.effect_stack.nodes):
        marker = ">" if index == state.selected_effect_index else " "
        enabled = "on" if node.enabled else "byp"
        table.add_row(
            f"{marker}{index}", node.type_name, enabled, str(node.params)
        )


def refresh_params_panel(
    panel: TextPanel,
    state: SessionState,
    slider_lines: list[str],
) -> None:
    node = state.selected_effect
    if node is None:
        panel.set("no effect selected")
        return
    effect = state.effect_stack.registry.create(node.type_name)
    params = effect.parameters.validate(node.params)
    lines = [
        "look sliders:",
        *slider_lines,
        "",
        f"{effect.display_name}",
        f"type: {node.type_name}",
        "params:",
    ]
    lines.extend(f"  {key}: {value}" for key, value in params.items())
    panel.set("\n".join(lines))


def refresh_export_panel(panel: TextPanel, state: SessionState) -> None:
    output = state.project.output
    queue = (
        "\n".join(f"  {job.kind}: {job.status}" for job in state.export_queue[-5:])
        or "  idle"
    )
    panel.set(
        f"video: {output.video_path}\n"
        f"image: {output.image_path}\n"
        f"mode: {output.render_mode}\n"
        f"queue:\n{queue}"
    )


def refresh_audio_panel(panel: TextPanel, state: SessionState) -> None:
    audio = state.project.audio
    panel.set(
        f"enabled: {audio.enabled}\n"
        f"waveform points: {audio.waveform_resolution}\n"
        f"window: {audio.analysis_window_seconds:.2f}s\n"
        f"status: silent analyzer"
    )
