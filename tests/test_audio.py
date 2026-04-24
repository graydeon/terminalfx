import numpy as np

from terminalfx.audio.features import analyze_samples, waveform_summary


def test_audio_features_and_waveform_summary() -> None:
    sample_rate = 48_000
    t = np.linspace(0, 1, sample_rate, endpoint=False)
    samples = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    features = analyze_samples(samples, sample_rate)
    summary = waveform_summary(samples, sample_rate, resolution=32)

    assert features.rms > 0
    assert features.peak > 0.9
    assert len(summary.samples) == 32
    assert summary.duration_seconds == 1.0
