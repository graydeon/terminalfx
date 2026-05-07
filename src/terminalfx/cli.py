from __future__ import annotations

from pathlib import Path
from time import monotonic

import typer

from terminalfx.config import load_project
from terminalfx.config.loader import to_plain_data
from terminalfx.config.schema import ProjectConfig
from terminalfx.effects.stack import EffectStack
from terminalfx.preview.window import run_preview_window
from terminalfx.render.offline import render_mp4, render_png
from terminalfx.render.pipeline import RenderPipeline
from terminalfx.render.realtime import record_realtime
from terminalfx.sources import create_source
from terminalfx.sources.base import SourceProvider
from terminalfx.tui.app import TerminalFxApp

app = typer.Typer(help="Offline terminal-style video effects workstation")


@app.command()
def tui(config: Path = Path("examples/configs/default.yaml")) -> None:
    """Open the keyboard-first Textual control surface."""
    TerminalFxApp(config).run()


@app.command("preview-window")
def preview_window(config: Path = Path("examples/configs/default.yaml")) -> None:
    """Open the dedicated external preview window."""
    run_preview_window(config)


@app.command("render-png")
def render_png_command(
    config: Path = Path("examples/configs/default.yaml"),
    output: Path | None = None,
) -> None:
    """Render one processed frame to PNG."""
    project = load_project(config)
    out_path = output or project.output.image_path
    with _pipeline(project) as pipeline:
        path = render_png(pipeline, out_path)
    typer.echo(path)


@app.command("render-mp4")
def render_mp4_command(
    config: Path = Path("examples/configs/default.yaml"),
    output: Path | None = None,
    frames: int = 180,
) -> None:
    """Render a short offline MP4 using the configured source and effects."""
    project = load_project(config)
    out_path = output or project.output.video_path
    with _pipeline(project) as pipeline:
        path = render_mp4(pipeline, project, out_path, frames)
    typer.echo(path)


@app.command("record")
def record_command(
    config: Path = Path("examples/configs/default.yaml"),
    output: Path | None = None,
    seconds: float = 3.0,
) -> None:
    """Record a realtime MP4 from the configured source."""
    project = load_project(config)
    out_path = output or project.output.video_path
    with _pipeline(project) as pipeline:
        path = record_realtime(pipeline, project, out_path, seconds)
    typer.echo(path)


@app.command("show-config")
def show_config(config: Path = Path("examples/configs/default.yaml")) -> None:
    """Print normalized project configuration."""
    import yaml

    typer.echo(yaml.safe_dump(to_plain_data(load_project(config)), sort_keys=False))


@app.command("config-doctor")
def config_doctor(config: Path = Path("examples/configs/default.yaml")) -> None:
    """Validate config and show source/effect summary."""
    project = load_project(config)
    stack = EffectStack.from_config(project.effects)
    typer.echo(f"project: {project.project_name}")
    typer.echo(f"source: {project.source.kind}")
    resolution = project.resolution
    typer.echo(f"resolution: {resolution.width}x{resolution.height}@{resolution.fps}")
    typer.echo(f"effects: {len(stack.nodes)}")
    typer.echo("ok")


@app.command("bench-fps")
def bench_fps(
    config: Path = Path("examples/configs/default.yaml"),
    seconds: float = 5.0,
    warmup: float = 1.0,
) -> None:
    """Benchmark raw pipeline FPS — no display, no TUI, no transport.

    This measures pure processing throughput. If this shows 30+ FPS
    but the preview window shows <30, the bottleneck is cv2.imshow/X11.
    """
    project = load_project(config)
    source = create_source(project.source, project.resolution)
    source.open()

    try:
        pipeline = RenderPipeline(
            source, EffectStack.from_config(project.effects), project
        )

        typer.echo(f"warming up for {warmup}s...")
        warmup_end = monotonic() + warmup
        while monotonic() < warmup_end:
            pipeline.render_next(project.preview.mode)

        typer.echo(f"benchmarking for {seconds}s...")
        frames = 0
        bench_end = monotonic() + seconds
        t0 = monotonic()
        while monotonic() < bench_end:
            pkt = pipeline.render_next(project.preview.mode)
            if pkt is None:
                typer.echo("WARNING: source exhausted, breaking early")
                break
            frames += 1

        elapsed = monotonic() - t0
        fps = frames / elapsed if elapsed > 0 else 0

        typer.echo(f"\n{'='*50}")
        typer.echo(f"  source:       {project.source.kind}")
        typer.echo(
            f"  resolution:   {project.resolution.width}x{project.resolution.height}"
        )
        typer.echo(f"  effects:      {len(pipeline.effect_stack.nodes)} enabled")
        typer.echo(f"  frames:       {frames}")
        typer.echo(f"  elapsed:      {elapsed:.2f}s")
        typer.echo(f"  FPS:          {fps:.1f}")
        if fps > 0:
            typer.echo(f"  ms/frame:     {1000 / fps:.1f}")
        typer.echo(f"{'='*50}")

        if fps >= 30:
            typer.echo(
                "\nPipeline is fast. If preview shows <30 FPS, "
                "bottleneck is cv2.imshow/X11 display."
            )
        else:
            typer.echo(
                "\nPipeline below 30 FPS. Try:\n"
                "  1. Reduce resolution in config\n"
                "  2. Disable effects (set enabled: false)\n"
                "  3. Use PIXEL mode (set preview.mode: pixel)\n"
                "  4. Match config resolution to source resolution"
            )
    finally:
        source.close()


class _pipeline:
    def __init__(self, project: ProjectConfig) -> None:
        self.project = project
        self.source: SourceProvider | None = None

    def __enter__(self) -> RenderPipeline:
        project = self.project
        source = create_source(project.source, project.resolution)
        source.open()
        self.source = source
        return RenderPipeline(source, EffectStack.from_config(project.effects), project)

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self.source is not None:
            self.source.close()


if __name__ == "__main__":
    app()
