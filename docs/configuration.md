# Configuration

`terminalfx` projects are configured with YAML. The file describes portable
project intent: resolution, source, preview routing, effect defaults, audio
behavior, and output paths.

Relative paths are resolved from the YAML file location.

Start from the safe default:

```bash
cp examples/configs/default.yaml my-project.yaml
terminalfx show-config --config my-project.yaml
```

## Top-Level Fields

| Field | Purpose |
| --- | --- |
| `project_name` | Human-readable project name |
| `resolution` | Output width, height, and frame rate |
| `preview` | Preview routing and display behavior |
| `source` | File, camera, screen, or window input |
| `effects` | Ordered effect stack |
| `audio` | Audio metadata and waveform behavior |
| `output` | Render and still-image targets |

## Source

Use one source kind at a time:

```yaml
source:
  kind: file
  path: media/input.mp4
  camera_index: 0
  screen_index: 0
  window_title: null
  loop: true
```

For `camera`, `screen`, or `window`, set `kind` and the matching field. The
default config uses `mock` so it does not reference local media or capture a
desktop target by accident.

## Preview

```yaml
preview:
  enabled: true
  mode: auto
  refresh_hz: 60
  fullscreen: false
  display_index: 0
  transport_path: run/preview-state.json
```

Use `mode: ascii` to force ASCII rendering or `mode: pixel` to preview processed
frames without ASCII conversion. For a dual-display setup, set
`display_index` to the preview monitor and `fullscreen` to `true`.

## Effects

Effects are stored as an ordered list:

```yaml
effects:
  - type: ascii_quantize
    label: ASCII levels
    enabled: true
    params:
      levels: 9
      invert: false
      contrast: 1.15
      brightness: 0.0
  - type: terminal_tint
    label: Green phosphor
    enabled: true
    params:
      palette: green
      scanlines: true
      intensity: 0.85
```

Effect presets should remain portable. Prefer relative paths and named presets
over machine-specific absolute paths.

The TUI exposes live look sliders for ASCII density, contrast, brightness,
quantization levels, and tint intensity. Density updates
`preview.character_width` and `preview.character_height`; the other sliders edit
the matching effect parameters in the active stack.

## Output

```yaml
output:
  directory: output
  video_path: output/render.mp4
  image_path: output/frame.png
  codec: mp4v
  render_mode: offline
```

Use `offline` for deterministic export and `realtime` when recording the active
preview stream. Generated files should stay under `output/` unless a project
needs a different export directory.
