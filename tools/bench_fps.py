"""Direct FPS benchmark — bypasses TUI, transport, and OpenCV display.

Run this to see the raw pipeline throughput without any display overhead.
This proves whether the bottleneck is in processing or in display/X11.
"""

from __future__ import annotations

import sys
from pathlib import Path
from time import monotonic

import typer

from terminalfx.config import load_project
from terminalfx.effects.stack import EffectStack
from terminalfx.render.pipeline import RenderPipeline
from terminalfx.sources import create_source


def bench(config: Path, seconds: float = 5.0, warmup: float = 1.0) -> None:
    """Measure raw pipeline FPS (no display, no transport, no TUI)."""
    project = load_project(config)
    source = create_source(project.source, project.resolution)
    source.open()

    try:
        pipeline = RenderPipeline(
            source, EffectStack.from_config(project.effects), project
        )

        # Warmup: run for warmup seconds
        typer.echo(f"warming up for {warmup}s...")
        warmup_end = monotonic() + warmup
        while monotonic() < warmup_end:
            pipeline.render_next(project.preview.mode)

        # Benchmark
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
        typer.echo(f"  resolution:   {project.resolution.width}x{project.resolution.height}")
        typer.echo(f"  effects:      {len(pipeline.effect_stack.nodes)} enabled")
        typer.echo(f"  frames:       {frames}")
        typer.echo(f"  elapsed:      {elapsed:.2f}s")
        typer.echo(f"  FPS:          {fps:.1f}")
        typer.echo(f"  ms/frame:     {1000/fps:.1f}" if fps > 0 else "  ms/frame:     N/A")
        typer.echo(f"{'='*50}")

        if fps < 30:
            typer.echo(
                "\nFPS below 30 — try:\n"
                "  1. Reduce resolution in config (e.g. 960x540)\n"
                "  2. Disable effects (set enabled: false)\n"
                "  3. Use PIXEL mode (set preview.mode: pixel)\n"
                "  4. Match config resolution to source resolution\n"
            )
        else:
            typer.echo("\nPipeline is fast — bottleneck is display (cv2.imshow/X11).")

    finally:
        source.close()


if __name__ == "__main__":
    typer.run(bench)
