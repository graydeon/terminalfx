# CLI Workflow

The `terminalfx` CLI is the entry point for configuration inspection,
interactive control, preview routing, and export workflows.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Runtime preview and capture features require a graphical desktop session.
Camera, screen, and window capture may also require operating-system permission.

## Commands

Inspect the active configuration:

```bash
terminalfx show-config --config examples/configs/default.yaml
```

Launch the Textual control surface:

```bash
terminalfx tui --config examples/configs/default.yaml
```

Launch only the preview window:

```bash
terminalfx preview-window --config examples/configs/default.yaml
```

Validate a project file:

```bash
terminalfx config-doctor --config examples/configs/default.yaml
```

Export a still frame or short offline video:

```bash
terminalfx render-png --config examples/configs/default.yaml
terminalfx render-mp4 --config examples/configs/default.yaml --frames 180
```

Record realtime output from the configured source:

```bash
terminalfx record --config examples/configs/default.yaml --seconds 3
```

## Typical Session

1. Copy `examples/configs/default.yaml` to a project-specific YAML file.
2. Set `source.kind` and the matching source field.
3. Set `preview.display_index` and `preview.fullscreen` for the target display.
4. Start `terminalfx tui --config <project>.yaml`.
5. Press `o` to open preview output.
6. Edit the effect stack from the keyboard.
7. Press `e` to enqueue export or `r` to arm realtime recording.

## Source Modes

- `mock`: generate local placeholder frames for safe first runs
- `file`: read frames from `source.path`
- `camera`: read from `source.camera_index`
- `screen`: capture `source.screen_index`
- `window`: capture the window matching `source.window_title`

The default config uses `mock` and does not start camera, screen, or window
capture automatically.

## Output

The v1 output contract is:

- MP4 video at `output.video_path`
- PNG still frame at `output.image_path`
- `realtime` mode for recording the active preview stream
- `offline` mode for deterministic high-quality rendering
