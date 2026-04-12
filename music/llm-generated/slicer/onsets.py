"""Onset detection and slice point generation."""

import random
from typing import List, Optional
import numpy as np
import librosa

from zero_crossing import snap_all


def detect(
    mono: np.ndarray,
    sr: int,
    min_intervals: Optional[int] = None,
    max_intervals: Optional[int] = None,
    glitchy: bool = False,
    min_ms: Optional[float] = None,
    max_ms: Optional[float] = None,
    zero_crossing_window_ms: float = 12.0,
) -> List[int]:
    """Compute slice boundary positions (in samples).

    In normal mode returns positions snapped to zero-crossings.
    In glitchy mode returns time-based positions with no snapping.

    The returned list does NOT include 0 or len(mono); callers should treat
    those as implicit start/end boundaries.
    """
    if glitchy:
        return _glitchy_positions(mono, sr, min_ms, max_ms)

    raw = _onset_positions(mono, sr)
    markers = _apply_interval_constraints(raw, min_intervals, max_intervals)

    window = int(zero_crossing_window_ms * sr / 1000)
    return snap_all(mono, markers, window_samples=window)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _onset_positions(mono: np.ndarray, sr: int) -> List[int]:
    """Detect onset positions using librosa, returned as sample indices."""
    onset_frames = librosa.onset.onset_detect(
        y=mono,
        sr=sr,
        units="samples",
        backtrack=True,          # snap onset to preceding local energy minimum
        hop_length=512,
    )
    positions = sorted(set(int(p) for p in onset_frames))
    # Remove any onset at sample 0 — the implicit file start is not a marker
    return [p for p in positions if p > 0]


def _apply_interval_constraints(
    positions: List[int],
    min_intervals: Optional[int],
    max_intervals: Optional[int],
) -> List[int]:
    """Merge or split detected onset positions to satisfy min/max interval counts.

    "Intervals" here means the number of consecutive detected onset gaps that
    a single slice may span.  min=2 → each slice covers >= 2 onset gaps.
    max=4 → each slice covers <= 4 onset gaps.
    """
    if not positions:
        return positions

    if min_intervals is not None and min_intervals > 1:
        positions = _merge_short(positions, min_intervals)

    if max_intervals is not None:
        positions = _split_long(positions, max_intervals)

    return positions


def _merge_short(positions: List[int], min_intervals: int) -> List[int]:
    """Merge consecutive onsets so each slice spans >= min_intervals gaps."""
    result = []
    # Walk the full onset list, emitting a boundary every min_intervals steps
    for i in range(0, len(positions), min_intervals):
        result.append(positions[i])
    return result


def _split_long(positions: List[int], max_intervals: int) -> List[int]:
    """Insert intermediate onsets so no slice spans > max_intervals gaps.

    When the detected onsets between two selected boundaries exceed max_intervals,
    we select an intermediate onset to split the span.
    """
    if len(positions) <= max_intervals:
        return positions  # nothing to split

    result = []
    i = 0
    while i < len(positions):
        result.append(positions[i])
        # Find how far ahead we can look before exceeding max_intervals
        next_boundary = i + max_intervals
        if next_boundary < len(positions):
            i = next_boundary
        else:
            # Include remaining tail on next iteration
            i += 1

    return result


def _glitchy_positions(
    mono: np.ndarray,
    sr: int,
    min_ms: Optional[float],
    max_ms: Optional[float],
) -> List[int]:
    """Generate time-based slice boundaries with no zero-crossing snapping."""
    min_ms = min_ms if min_ms is not None else 100.0
    max_ms = max_ms if max_ms is not None else 500.0

    min_samples = max(1, int(min_ms * sr / 1000))
    max_samples = max(min_samples, int(max_ms * sr / 1000))

    total = len(mono)
    positions = []
    cursor = 0
    while cursor < total:
        step = random.randint(min_samples, max_samples)
        cursor += step
        if cursor < total:
            positions.append(cursor)

    return positions
