# Architecture

`terminalfx` is organized as a small workstation pipeline: select a source,
process frames through an ordered effect stack, preview the result, then record
or export.

## Product Identity

`terminalfx` focuses on terminal-native and terminal-inspired visual effects:
ASCII conversion, phosphor display looks, scanlines, monochrome palettes, pixel
preview, and dense keyboard control. It is not a general nonlinear editor.

V1 is scoped to:

- one active file, camera, screen, or window source
- one ordered effect stack
- one Textual control surface
- one external preview window
- realtime recording and offline MP4 / PNG export

## Runtime Components

The module layout is designed around clear ownership boundaries:

- `core`: shared types, time values, frame packets, and errors
- `config`: YAML loading, validation, and serialization
- `sources`: source adapters for mock frames, video files, cameras, screens, and windows
- `effects`: frame transforms, effect presets, bypass state, and parameters
- `session`: session state, transport state, and pipeline coordination
- `tui`: Textual widgets, focus model, keybindings, and command palette actions
- `preview`: borderless or windowed preview output on a selected display
- `render`: offline export, realtime recording, image export, and frame writing
- `audio`: audio presence, waveform summaries, and reactive-effect hooks
- `persistence`: project and preset persistence

## Data Flow

1. A YAML project config is loaded.
2. The active source produces frames normalized to the project resolution.
3. Frames pass through the ordered effect stack.
4. The TUI updates session state and writes preview state.
5. The preview window reads session state and presents low-latency output.
6. Render and record commands write MP4, PNG, or frame-sequence output.

The TUI is responsible for state editing. The preview window is responsible for
visual output. That split keeps keyboard interaction responsive while preserving
a clean, fullscreen preview for review or capture.

## Display Model

The preferred workflow uses two displays:

- display 0: terminal control surface
- display 1: dedicated preview output

The default config uses display `0` and non-fullscreen preview behavior so first
runs are safe on laptops and single-monitor systems. Set `preview.display_index`
and `preview.fullscreen` for a studio or dual-monitor setup.

## Configuration Boundary

Configuration should describe portable project intent: source mode, preview
routing, effect defaults, audio behavior, and output paths. Session-only data,
such as current focus, selected effect row, play state, and temporary logs,
belongs in runtime state instead of the saved project file.

## Extension Points

New capabilities should enter through the narrowest matching boundary:

- add a source adapter under `sources`
- add frame processing under `effects`
- add export targets under `render`
- add interaction affordances under `tui`
- add display behavior under `preview`

This keeps the terminal control surface, preview output, and render path from
depending on each other directly.
