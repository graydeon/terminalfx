from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

import numpy as np
from PIL import ImageGrab

from terminalfx.core.errors import SourceError
from terminalfx.core.types import FramePacket, SourceKind, TimePoint
from terminalfx.sources.base import SourceCapabilities, SourceInfo


@dataclass(frozen=True, slots=True)
class MonitorInfo:
    index: int
    name: str
    x: int
    y: int
    width: int
    height: int


def parse_xrandr_monitors(output: str) -> list[MonitorInfo]:
    pattern = re.compile(
        r"\s*(\d+):\s+\+\*?([^\s]+)\s+(\d+)/(?:\d+)x(\d+)/(?:\d+)\+(-?\d+)\+(-?\d+)"
    )
    monitors: list[MonitorInfo] = []
    for line in output.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        index, name, width, height, x, y = match.groups()
        monitors.append(MonitorInfo(int(index), name, int(x), int(y), int(width), int(height)))
    return monitors


def list_monitors() -> list[MonitorInfo]:
    proc = subprocess.run(["xrandr", "--listmonitors"], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return []
    return parse_xrandr_monitors(proc.stdout)


def parse_wmctrl_titles(output: str) -> list[str]:
    titles: list[str] = []
    for line in output.splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4 and parts[3].strip() not in titles:
            titles.append(parts[3].strip())
    return titles


def list_window_titles() -> list[str]:
    proc = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return []
    return parse_wmctrl_titles(proc.stdout)


def _window_geometry(title_query: str) -> tuple[int, int, int, int] | None:
    windows = subprocess.run(["wmctrl", "-l"], capture_output=True, text=True, check=False)
    if windows.returncode != 0:
        return None
    query = title_query.lower()
    window_id: str | None = None
    for line in windows.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4 and query in parts[3].lower():
            window_id = parts[0]
            break
    if window_id is None:
        return None
    info = subprocess.run(
        ["xwininfo", "-id", window_id], capture_output=True, text=True, check=False
    )
    if info.returncode != 0:
        return None
    x = re.search(r"Absolute upper-left X:\s+(-?\d+)", info.stdout)
    y = re.search(r"Absolute upper-left Y:\s+(-?\d+)", info.stdout)
    width = re.search(r"Width:\s+(\d+)", info.stdout)
    height = re.search(r"Height:\s+(\d+)", info.stdout)
    if x is None or y is None or width is None or height is None:
        return None
    return int(x.group(1)), int(y.group(1)), int(width.group(1)), int(height.group(1))


class ScreenSource:
    def __init__(self, screen_index: int = 0, fps: float = 60.0) -> None:
        self.screen_index = screen_index
        self.fps = fps
        self._monitor: MonitorInfo | None = None
        self._frame_index = 0

    def open(self) -> SourceInfo:
        monitors = list_monitors()
        if not monitors:
            raise SourceError("no monitors discovered")
        self._monitor = monitors[self.screen_index % len(monitors)]
        return SourceInfo(
            kind=SourceKind.SCREEN,
            name=self._monitor.name,
            width=self._monitor.width,
            height=self._monitor.height,
            fps=self.fps,
            capabilities=SourceCapabilities(seekable=False, live=True),
        )

    def read(self, time: TimePoint | None = None) -> FramePacket | None:
        if self._monitor is None:
            raise SourceError("screen source is not open")
        image = ImageGrab.grab(
            bbox=(
                self._monitor.x,
                self._monitor.y,
                self._monitor.x + self._monitor.width,
                self._monitor.y + self._monitor.height,
            ),
            all_screens=True,
        )
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
        frame = rgb[:, :, ::-1].copy()
        point = TimePoint(seconds=self._frame_index / self.fps, frame=self._frame_index)
        self._frame_index += 1
        return FramePacket(frame=frame, time=point, source_name=self._monitor.name)

    def seek(self, time: TimePoint) -> None:
        raise SourceError("screen sources are not seekable")

    def close(self) -> None:
        self._monitor = None


class WindowSource:
    def __init__(self, title: str, fps: float = 60.0) -> None:
        self.title = title
        self.fps = fps
        self._geometry: tuple[int, int, int, int] | None = None
        self._frame_index = 0

    def open(self) -> SourceInfo:
        geometry = _window_geometry(self.title)
        if geometry is None:
            raise SourceError(f"window not found: {self.title}")
        self._geometry = geometry
        _, _, width, height = geometry
        return SourceInfo(
            kind=SourceKind.WINDOW,
            name=self.title,
            width=width,
            height=height,
            fps=self.fps,
            capabilities=SourceCapabilities(seekable=False, live=True),
        )

    def read(self, time: TimePoint | None = None) -> FramePacket | None:
        if self._geometry is None:
            raise SourceError("window source is not open")
        x, y, width, height = self._geometry
        image = ImageGrab.grab(bbox=(x, y, x + width, y + height), all_screens=True)
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
        point = TimePoint(seconds=self._frame_index / self.fps, frame=self._frame_index)
        self._frame_index += 1
        return FramePacket(frame=rgb[:, :, ::-1].copy(), time=point, source_name=self.title)

    def seek(self, time: TimePoint) -> None:
        raise SourceError("window sources are not seekable")

    def close(self) -> None:
        self._geometry = None
