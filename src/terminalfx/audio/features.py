from __future__ import annotations

import math

import numpy as np

from terminalfx.core.types import AudioFeatures, WaveformSummary


def analyze_samples(samples: np.ndarray, sample_rate: int) -> AudioFeatures:
    if samples.size == 0:
        return AudioFeatures()
    mono = _mono(samples)
    rms = float(np.sqrt(np.mean(np.square(mono))))
    peak = float(np.max(np.abs(mono)))
    spectrum = np.abs(np.fft.rfft(mono))
    if spectrum.size == 0:
        return AudioFeatures(rms=rms, peak=peak)
    freqs = np.fft.rfftfreq(mono.size, d=1 / sample_rate)
    low = _band_energy(spectrum, freqs, 20, 250)
    mid = _band_energy(spectrum, freqs, 250, 4000)
    high = _band_energy(spectrum, freqs, 4000, sample_rate / 2)
    return AudioFeatures(rms=rms, peak=peak, low=low, mid=mid, high=high)


def waveform_summary(samples: np.ndarray, sample_rate: int, resolution: int) -> WaveformSummary:
    if resolution <= 0:
        raise ValueError("resolution must be positive")
    mono = _mono(samples)
    if mono.size == 0:
        return WaveformSummary(samples=(), sample_rate=sample_rate, duration_seconds=0.0)
    bins = np.array_split(mono, resolution)
    peaks = tuple(float(np.max(np.abs(item))) if item.size else 0.0 for item in bins)
    return WaveformSummary(
        samples=peaks,
        sample_rate=sample_rate,
        duration_seconds=float(mono.size / sample_rate),
    )


class SilentAudioAnalyzer:
    def analyze_window(self, seconds: float) -> AudioFeatures:
        pulse = max(0.0, math.sin(seconds * math.pi * 2.0)) * 0.0
        return AudioFeatures(rms=pulse, peak=pulse)

    def waveform_summary(self, resolution: int) -> WaveformSummary:
        return WaveformSummary(
            samples=tuple(0.0 for _ in range(resolution)), sample_rate=48_000, duration_seconds=0.0
        )


class SampleAudioAnalyzer:
    """Real audio analyzer backed by pre-extracted audio samples."""

    def __init__(self, samples: np.ndarray, sample_rate: int) -> None:
        self._samples = _mono(samples)
        self._sample_rate = sample_rate
        self._duration = (
            float(len(self._samples) / sample_rate) if sample_rate > 0 else 0.0
        )

    def analyze_window(self, seconds: float) -> AudioFeatures:
        if self._samples.size == 0:
            return AudioFeatures()
        center = int(seconds * self._sample_rate)
        half_window = int(0.5 * self._sample_rate)
        start = max(0, center - half_window)
        end = min(len(self._samples), center + half_window)
        window = self._samples[start:end]
        if window.size == 0:
            return AudioFeatures()
        return analyze_samples(window, self._sample_rate)

    def waveform_summary(self, resolution: int) -> WaveformSummary:
        return waveform_summary(self._samples, self._sample_rate, resolution)


def _mono(samples: np.ndarray) -> np.ndarray:
    data = samples.astype(np.float32)
    if data.ndim > 1:
        data = data.mean(axis=1)
    peak = np.max(np.abs(data)) if data.size else 0.0
    if peak > 1.0:
        data = data / peak
    return data


def _band_energy(spectrum: np.ndarray, freqs: np.ndarray, low: float, high: float) -> float:
    mask = (freqs >= low) & (freqs < high)
    if not np.any(mask):
        return 0.0
    return float(np.mean(spectrum[mask]))
