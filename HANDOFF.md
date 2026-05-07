# terminalfx — Handoff

Last updated: 2026-05-06

## State

Alpha-ready. 58 tests pass, ruff clean, mypy strict clean.
Pipeline benchmarks at 45 FPS at 640×360 with 2 effects active.

## What Was Done (2026-05-06 session)

Full execution of the code review at `/home/gray/Documents/terminalfx code review`.
All 10 findings addressed, plus 9 additional improvements.

### Critical Fixes
- `all_screens=True` → `False` in screen.py (silent multi-monitor data corruption)
- PreviewConfig defaults: `display_index=0, fullscreen=False` (match docs)
- normalize_frame zero-dim crash → returns blank frame

### High Fixes
- Export queue wired to background worker thread (was dead-letter accumulator)
- Audio extraction from video files via ffprobe/ffmpeg
- SampleAudioAnalyzer with real FFT bands (was SilentAudioAnalyzer always)

### Medium Fixes
- Effect type cycling (a key cycles through registry, was hardcoded phosphor_trail)
- MP4 export from TUI (e=PNG, E=MP4)
- Per-type preset filenames (was single hardcoded file)
- node_id preserved in stack round-trip
- Encoder mkdir after writer check (no orphan dirs on failure)
- media/__init__.py exports
- Preview cancellation signal (O key)
- Bidirectional preview transport (preview → TUI status messages)

### Performance (5 FPS → 45 FPS)
- Resolution default: 1920×1080 → 640×360
- Camera source: simple blocking read (no threaded reader race condition)
- Preview window sized to project resolution (was monitor resolution, causing GPU upscale)
- Transport mtime cache + dedup (no disk I/O per frame)
- normalize_frame fast-path when dimensions match
- Effect param validation cache
- AUTO mode → PIXEL for live sources
- frame_to_ascii: PIL → OpenCV (no BGR→RGB copy)
- ascii_to_frame_fast with pre-rendered glyph atlas
- Mock source: precomputed gradients
- Snapshot change detection (skip dict parsing when unchanged)
- json.dumps removed from hot path
- PassthroughEffect no-copy

### Architecture
- tui/ split: widgets.py, bindings.py, panels.py, look_controls.py, export_worker.py
- CI/CD: .github/workflows/ci.yml (ruff + mypy + pytest + smoke, python 3.11/3.12)

### New Tests (15 → 58)
- test_cli.py: render-png, render-mp4, record, config-doctor, help
- test_config_comprehensive.py: defaults, invalid YAML, schema rejection
- test_effects_comprehensive.py: node_id round-trip, unknown effect, registry
- test_encoder.py: encode, bad codec, write_png
- test_normalize.py: zero-dim, single-pixel, extreme aspect
- test_session_comprehensive.py: export queue, source cycle, preset round-trip

### New Commands
- `terminalfx bench-fps`: raw pipeline benchmark (no display, no TUI)
- Per-phase frame timing in preview status (read_ms, snap_ms, pipe_ms, rend_ms, show_ms)

### New Configs
- `examples/configs/live-camera.yaml`: 960×540, 1 effect, camera source — optimized for live use
- `examples/configs/bench-2fx.yaml`: 640×360, 2 effects — for benchmarking
- `examples/configs/bench-960.yaml`: 960×540, 1 effect — for benchmarking

### New Tools
- `tools/preview_standalone.py`: standalone preview with FPS reporting (no TUI needed)
- `tools/bench_fps.py`: standalone FPS benchmark script

## Key Files Modified

```
examples/configs/default.yaml        — resolution 1920×1080→640×360, refresh_hz 60→30
src/terminalfx/sources/camera.py     — simple blocking read, no threading
src/terminalfx/sources/screen.py     — all_screens=False fix
src/terminalfx/sources/video_file.py — ffprobe/ffmpeg audio extraction
src/terminalfx/sources/mock.py       — precomputed gradients
src/terminalfx/effects/builtins.py   — no-copy passthrough, inline conversion
src/terminalfx/effects/stack.py      — param validation cache, node_id round-trip
src/terminalfx/media/frames.py       — fast-path, OpenCV ascii, glyph atlas
src/terminalfx/preview/window.py     — frame timing, snapshot cache, window sizing
src/terminalfx/preview/transport.py  — mtime cache, dedup, bidirectional
src/terminalfx/preview/renderer.py   — PIXEL fast path, AUTO→PIXEL for live
src/terminalfx/preview/controller.py — stop/request_stop
src/terminalfx/render/pipeline.py    — audio auto-detection
src/terminalfx/render/encoders.py    — mkdir ordering
src/terminalfx/config/schema.py      — safe defaults
src/terminalfx/core/types.py         — 640×360@30 defaults
src/terminalfx/cli.py                — bench-fps command
src/terminalfx/tui/app.py            — split into submodules
src/terminalfx/tui/bindings.py       — NEW
src/terminalfx/tui/widgets.py        — NEW
src/terminalfx/tui/panels.py         — NEW
src/terminalfx/tui/look_controls.py  — NEW
src/terminalfx/tui/export_worker.py  — NEW
.github/workflows/ci.yml             — NEW
```

## Performance Notes

Resolution is the #1 FPS driver. Each doubling of pixel count costs ~4× in processing time.

| Resolution | Pixels | FPS (2 effects) |
|---|---|---|
| 640×360 | 0.23M | 45 FPS |
| 960×540 | 0.52M | ~21 FPS |
| 1280×720 | 0.92M | ~13 FPS |
| 1920×1080 | 2.07M | ~5 FPS |

For 30+ FPS with 2 effects, stay at 640×360 or below.
For higher resolutions, reduce effect count or accept lower FPS.

## Quick Start

```bash
cd /home/gray/dev/terminalfx
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
terminalfx tui --config examples/configs/default.yaml
```

TUI keys: `o`=preview, `m`=source, `p`=mode, `e`=export PNG, `E`=export MP4, `q`=quit.
