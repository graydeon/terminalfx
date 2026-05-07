from __future__ import annotations

import subprocess
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import cast

import cv2
import numpy as np

from terminalfx.audio.extract import read_wav
from terminalfx.core.errors import SourceError
from terminalfx.core.types import Frame, FramePacket, SourceKind, TimePoint
from terminalfx.sources.base import SourceCapabilities, SourceInfo


class VideoFileSource:
    def __init__(self, path: Path, loop: bool = True) -> None:
        self.path = path
        self.loop = loop
        self._capture: cv2.VideoCapture | None = None
        self._info: SourceInfo | None = None
        self._frame_index = 0
        self._audio_samples: np.ndarray | None = None
        self._audio_sample_rate: int = 0

    def open(self) -> SourceInfo:
        capture = cv2.VideoCapture(str(self.path))
        if not capture.isOpened():
            raise SourceError(f"unable to open video file: {self.path}")
        self._capture = capture
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frame_count / fps if fps and frame_count else None

        has_audio = self._detect_audio()
        if has_audio:
            self._extract_audio()

        self._info = SourceInfo(
            kind=SourceKind.FILE,
            name=self.path.name,
            width=width,
            height=height,
            fps=fps,
            duration_seconds=duration,
            capabilities=SourceCapabilities(seekable=True, live=False, has_audio=has_audio),
        )
        self._frame_index = 0
        return self._info

    @property
    def audio_samples(self) -> np.ndarray | None:
        return self._audio_samples

    @property
    def audio_sample_rate(self) -> int:
        return self._audio_sample_rate

    def read(self, time: TimePoint | None = None) -> FramePacket | None:
        if self._capture is None:
            raise SourceError("video source is not open")
        if time is not None:
            self.seek(time)
        ok, frame = self._capture.read()
        if not ok and self.loop:
            self.seek(TimePoint())
            ok, frame = self._capture.read()
        if not ok:
            return None
        info = self._require_info()
        frame_index = int(self._capture.get(cv2.CAP_PROP_POS_FRAMES) or self._frame_index)
        point = TimePoint(seconds=max(0, frame_index - 1) / info.fps, frame=max(0, frame_index - 1))
        self._frame_index = frame_index
        return FramePacket(frame=cast(Frame, frame), time=point, source_name=info.name)

    def seek(self, time: TimePoint) -> None:
        if self._capture is None:
            raise SourceError("video source is not open")
        frame_index = time.frame
        if frame_index <= 0 and time.seconds > 0:
            frame_index = int(time.seconds * self._require_info().fps)
        self._capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        self._frame_index = frame_index

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
        self._capture = None

    def _require_info(self) -> SourceInfo:
        if self._info is None:
            raise SourceError("video source metadata is unavailable")
        return self._info

    def _detect_audio(self) -> bool:
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "a:0",
                    "-show_entries", "stream=codec_type",
                    "-of", "csv=p=0",
                    str(self.path),
                ],
                capture_output=True, text=True, timeout=10,
            )
            return "audio" in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _extract_audio(self) -> None:
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            subprocess.run(
                [
                    "ffmpeg", "-y", "-v", "error",
                    "-i", str(self.path),
                    "-vn", "-acodec", "pcm_s16le",
                    "-ar", "44100", "-ac", "1",
                    str(tmp_path),
                ],
                capture_output=True, timeout=30, check=True,
            )
            if tmp_path.stat().st_size > 44:  # WAV header minimum
                samples, sr = read_wav(tmp_path)
                self._audio_samples = samples
                self._audio_sample_rate = sr
        except (FileNotFoundError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired, OSError):
            pass
        finally:
            if "tmp_path" in locals() and tmp_path.exists():
                with suppress(OSError):
                    tmp_path.unlink()
