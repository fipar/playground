"""Zero-crossing utilities for pop-free slice boundary placement."""

from typing import List
import numpy as np


def find_nearest(mono: np.ndarray, position: int, window_samples: int = 512) -> int:
    """Return the sample index nearest to `position` that is a zero-crossing.

    Searches in [position - window_samples, position + window_samples].
    Falls back to `position` unchanged if no zero-crossing is found.
    """
    start = max(0, position - window_samples)
    end = min(len(mono) - 1, position + window_samples)

    segment = mono[start : end + 1]
    signs = np.sign(segment)
    # Replace exact zeros with +1 so they count as a crossing with negative neighbours
    signs[signs == 0] = 1

    crossings = np.where(np.diff(signs) != 0)[0]  # indices into segment
    if len(crossings) == 0:
        return position

    # Convert to absolute sample positions (crossing is between [i] and [i+1]; use i+1)
    absolute = crossings + 1 + start
    nearest = int(absolute[np.argmin(np.abs(absolute - position))])
    return nearest


def snap_all(mono: np.ndarray, positions: List[int], window_samples: int = 512) -> List[int]:
    """Snap every position in the list to its nearest zero-crossing."""
    return [find_nearest(mono, p, window_samples) for p in positions]
