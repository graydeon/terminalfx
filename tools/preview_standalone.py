# Standalone preview — run this directly to test FPS without the TUI.
# python tools/preview_standalone.py examples/configs/default.yaml

import sys
from pathlib import Path
from time import monotonic

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from terminalfx.config import load_project
from terminalfx.effects.stack import EffectStack
from terminalfx.preview.renderer import PreviewRenderer
from terminalfx.render.pipeline import RenderPipeline
from terminalfx.sources import create_source


def main():
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "examples/configs/default.yaml"
    )
    project = load_project(config_path)
    source = create_source(project.source, project.resolution)
    source.open()
    renderer = PreviewRenderer(project.preview)
    pipeline = RenderPipeline(
        source, EffectStack.from_config(project.effects), project
    )

    source_is_live = project.source.kind.value in {"camera", "screen", "window"}
    win = "terminalfx-preview"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win, project.resolution.width, project.resolution.height)

    frames = 0
    t0 = monotonic()
    last_report = t0

    print(f"source={project.source.kind} "
          f"res={project.resolution.width}x{project.resolution.height} "
          f"effects={len(pipeline.effect_stack.nodes)} "
          f"is_live={source_is_live}  q=quit")

    try:
        while True:
            pkt = pipeline.render_next(project.preview.mode)
            if pkt is None:
                cv2.waitKey(100)
                continue

            frame = renderer.render(
                pkt.frame, project.preview.mode,
                [f"FPS: ...", f"source: {project.source.kind}"],
                source_is_live=source_is_live,
            )
            cv2.imshow(win, frame)

            if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                break

            frames += 1
            now = monotonic()
            if now - last_report >= 2.0:
                fps = frames / (now - t0)
                print(f"  {frames} frames  {fps:.1f} FPS  "
                      f"{(now - t0) / frames * 1000:.1f}ms/frame")
                last_report = now
    finally:
        source.close()
        cv2.destroyWindow(win)


if __name__ == "__main__":
    main()
