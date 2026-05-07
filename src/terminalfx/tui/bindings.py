"""Keyboard binding definitions for the terminalfx TUI."""

from textual.binding import Binding

BINDINGS: list[Binding] = [
    Binding("q", "quit", "Quit"),
    Binding("o", "open_preview", "Preview"),
    Binding("O", "close_preview", "StopPrv"),
    Binding("m", "cycle_source", "Source"),
    Binding("c", "cycle_camera", "Camera"),
    Binding("S", "cycle_screen", "Screen"),
    Binding("w", "cycle_window", "Window"),
    Binding("p", "cycle_preview", "Mode"),
    Binding("space", "toggle_play", "Play"),
    Binding("r", "toggle_record", "Record"),
    Binding("e", "queue_export_png", "ExpPNG"),
    Binding("E", "queue_export_mp4", "ExpMP4"),
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

KEYS_HELP = (
    "o open preview\nO stop preview\nm source\n"
    "c camera\nS screen\nw window\np mode\n"
    "space play\nr record\ne export PNG\n"
    "E export MP4\nj/k select\nJ/K move\n"
    "a add\nx remove\nb bypass\nd duplicate\n"
    "n/N look slider\n[ and ] adjust\n"
    "s save preset\nl load preset"
)
