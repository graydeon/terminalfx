"""Background export worker for processing the export queue."""

import threading
from collections.abc import Callable
from pathlib import Path
from time import sleep

from terminalfx.render.offline import render_mp4, render_png
from terminalfx.render.pipeline import RenderPipeline
from terminalfx.session.model import ExportJob, SessionState
from terminalfx.sources import create_source


class ExportWorker:
    """Daemon thread that polls the export queue and processes jobs."""

    def __init__(
        self,
        refresh_view: Callable[..., None],
        get_state: Callable[[], SessionState],
    ) -> None:
        self._refresh_view = refresh_view
        self._get_state = get_state
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="export-worker"
        )
        self._thread.start()

    def _loop(self) -> None:
        while True:
            sleep(0.5)
            state = self._get_state()
            for job in state.export_queue:
                if job.status != "queued":
                    continue
                job.status = "processing"
                self._refresh_view()
                self._process_one(job, state)
                self._refresh_view()

    @staticmethod
    def _process_one(job: ExportJob, state: SessionState) -> None:
        try:
            source = create_source(state.project.source, state.project.resolution)
            source.open()
            try:
                pipeline = RenderPipeline(
                    source, state.effect_stack, state.project
                )
                if job.kind == "png":
                    render_png(pipeline, Path(job.path))
                elif job.kind == "mp4":
                    render_mp4(pipeline, state.project, Path(job.path), frames=180)
                job.status = "completed"
                state.append_log(f"export complete: {job.path}")
            finally:
                source.close()
        except Exception as exc:
            job.status = "failed"
            state.append_log(f"export failed: {job.path} ({exc})")
