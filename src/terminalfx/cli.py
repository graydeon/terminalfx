from __future__ import annotations

from pathlib import Path

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
