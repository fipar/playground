"""Audio loading utilities."""

import numpy as np
import soundfile as sf
import librosa


def load(path: str) -> tuple[np.ndarray, int]:
    """Load an audio file.

    Returns a tuple of (samples, sample_rate).
    samples is always a 2-D array of shape (num_samples, num_channels),
    float32, range [-1.0, 1.0].
    """
    try:
        data, sr = sf.read(path, always_2d=True, dtype="float32")
        return data, sr
    except Exception:
        # Fall back to librosa for formats soundfile can't handle (e.g. MP3)
        data_mono, sr = librosa.load(path, sr=None, mono=False)
        if data_mono.ndim == 1:
            data_mono = data_mono[np.newaxis, :]  # (1, N)
        # librosa returns (channels, samples); transpose to (samples, channels)
        return data_mono.T.astype(np.float32), sr


def to_mono(data: np.ndarray) -> np.ndarray:
    """Downmix to mono by averaging channels. Returns 1-D array."""
    if data.ndim == 1:
        return data
    return data.mean(axis=1)
