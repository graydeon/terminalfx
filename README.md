

# terminalfx

`terminalfx` is a keyboard-first visual effects workstation for terminal-style
imagery. It is built for offline scene building, clip processing, and live
source preview where the control surface stays in the terminal and the rendered
output is shown in a dedicated preview window.

The v1 product shape is intentionally focused:

- load a video file, camera feed, screen, or window source
- apply an ordered stack of ASCII, pixel, and terminal-look effects
- preview output in `auto`, `ascii`, or `pixel` mode
- record realtime output or export offline MP4 / PNG assets
- keep audio metadata available for waveform display and future reactive effects

## Architecture

`terminalfx` separates control, preview, and rendering concerns:

- `src/terminalfx/core` holds shared types and errors.
- `src/terminalfx/config` defines typed project configuration loaded from YAML.
- `src/terminalfx/sources` normalizes mock, file, camera, screen, and window inputs.
- `src/terminalfx/effects` owns composable frame effects and presets.
- `src/terminalfx/session` coordinates transport and runtime state.
- `src/terminalfx/tui` provides the Textual control surface.
- `src/terminalfx/preview` owns the external preview window.
- `src/terminalfx/render` writes video, image, and frame-sequence outputs.
- `src/terminalfx/audio` carries waveform and audio summary data.
- `src/terminalfx/persistence` handles saved projects and presets.

See [docs/architecture.md](docs/architecture.md) for the component model.

## Setup

`terminalfx` targets Python 3.11+ and a graphical desktop session for the
preview window.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
terminalfx --help
```

OpenCV-backed preview and capture features may require OS-level permissions for
camera, screen, and window capture.

## CLI Workflow

Start from the example config:

```bash
terminalfx show-config --config examples/configs/default.yaml
terminalfx tui --config examples/configs/default.yaml
```

From the TUI, press `o` to open the preview window. The preview can also be run
directly when testing display routing:

```bash
terminalfx preview-window --config examples/configs/default.yaml
```

See [docs/cli.md](docs/cli.md) for the expected command flow.

## Keyboard Model

The control surface is keyboard-first and uses compact, repeatable bindings:

- `tab` / `shift+tab` moves focus between panels
- `j` / `k` moves within lists
- `J` / `K` reorders the selected effect
- `a`, `x`, `b`, `d` add, remove, bypass, and duplicate effects
- `p` cycles preview mode
- `space`, `r`, `e` control playback, realtime record arm, and export queueing
- `q` quits the active terminal UI

See [docs/keyboard.md](docs/keyboard.md) for the full v1 binding map.

## Configuration

Project settings live in YAML. The default config uses a mock source and does
not reference a local media path, camera, screen, or window by default.

```bash
cp examples/configs/default.yaml my-shot.yaml
$EDITOR my-shot.yaml
terminalfx tui --config my-shot.yaml
```

See [docs/configuration.md](docs/configuration.md) for supported fields.
