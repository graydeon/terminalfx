from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class PreviewProcessController:
    def __init__(self, config_path: Path, log_path: Path) -> None:
        self.config_path = config_path.resolve()
        self.log_path = log_path.resolve()
        self.process: subprocess.Popen[str] | None = None

    def start(self) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        src_root = str(Path(__file__).resolve().parents[2])
        existing = env.get("PYTHONPATH")
        env["PYTHONPATH"] = src_root if not existing else f"{src_root}:{existing}"
        log_file = self.log_path.open("a")
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "terminalfx.cli",
                "preview-window",
                "--config",
                str(self.config_path),
            ],
            env=env,
            cwd=str(Path.cwd()),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
        log_file.close()
