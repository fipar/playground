#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced Audio Mosaicing with Pitch and Volume Tuning

This script extends the basic mosaic.py functionality by not only finding the
best matching source chunks, but also applying pitch and volume adjustments
to make each match even better.

Enhancements over mosaic.py:
- Pitch Tuning: After finding the best match, the source chunk's pitch is
  shifted to exactly match the reference chunk's pitch (like an auto-tuner).
- Volume Matching: The overall loudness (RMS) of the source chunk is scaled
  to match the reference chunk's loudness.
- Volume Envelope Matching: The dynamic volume changes over time (the envelope)
  are analyzed in the reference chunk and applied to the source chunk, creating
  a more natural and expressive match.
- Overlapping Chunks: Chunks can overlap for smoother transitions and better
  acoustic analysis (default 50% overlap).
- Windowing Functions: Applies windowing (Hann, Hamming, etc.) before FFT
  analysis to reduce spectral leakage and improve frequency analysis.
- Usage Tracking (Novelty): Tracks block usage and penalizes overused blocks
  to create more variety and avoid repetitive patterns.
- Stickyness: Preference for playing consecutive blocks from the same source
  file, preserving longer recognizable phrases and musical coherence.
- Chunk Caching: Analyzed chunks are cached in .mosaic-cache/ directory for
  faster repeated runs with the same input files.

Core Workflow:
1. Find the best matching source chunk (same as mosaic.py)
2. Apply pitch shift to match reference pitch
3. Apply volume scaling to match reference RMS
4. Apply volume envelope to match reference dynamics

Caching:
- Chunks are automatically cached in .mosaic-cache/ directory
- Cache is invalidated if input files change
- Significantly speeds up repeated runs with the same files

Future Enhancements (Not Yet Implemented):
Two additional features from Samplebrain could be added but involve significant complexity:

1. Dual Processing (Normal + Normalized):
   - What: Process each chunk twice - once with dynamics, once normalized
   - Benefit: Allows blending between "match timbre only" and "match timbre + dynamics"
   - Use Case: When you want to preserve source dynamics vs. match target dynamics
   - Complexity: Doubles memory usage, doubles analysis time, adds UI parameter
   - Implementation: Add m_n_fft, m_n_mfcc to AudioChunk, modify feature extraction

2. Synaptic Search Network:
   - What: Pre-build a similarity graph connecting each chunk to its 1000 nearest neighbors
   - Benefit: O(1) search time vs O(n) - massive speedup for large datasets (>10,000 chunks)
   - Use Case: When working with hours of source material (currently ~1-2min is fine)
   - Complexity: O(n²) preprocessing, complex data structure, 4-8GB RAM for large sets
   - Implementation: Add build_synapses() function, modify find_best_match() search logic

Current implementation is optimized for typical use cases (a few minutes of audio per source).
These enhancements would primarily benefit edge cases with very large source libraries.

Dependencies:
pip install numpy librosa soundfile tqdm scipy

Usage:
python tuned-mosaic.py \
    --reference path/to/reference.wav \
    --sources path/to/source1.wav path/to/source2.wav \
    --output path/to/output.wav \
    --chunk-size-min 0.1 \
    --chunk-size-max 0.4 \
    --overlap 0.5 \
    --window hann \
    --usage-importance 0.1 \
    --stickyness 0.5 \
    --enable-pitch-tuning \
    --enable-volume-tuning \
    --enable-envelope-tuning

"""

import argparse
import numpy as np
import librosa
import soundfile as sf
from tqdm import tqdm
from scipy.interpolate import interp1d
from scipy import signal
import warnings
import copy
import hashlib
import pickle
import os

# Suppress annoying librosa warnings
warnings.filterwarnings('ignore', category=UserWarning)

# --- Data Structure for an Audio Chunk ---
class AudioChunk:
    """A class to hold a chunk of audio and its features."""
    def __init__(self, audio_data, sample_rate, window_type='hann', source_file='', chunk_index=0):
        self.audio = audio_data
        self.sr = sample_rate
        self.window_type = window_type
        self.features = self._extract_features()
        # Normalized features added later
        self.norm_features = {}
        # Usage tracking for novelty (avoiding repetitive blocks)
        self.usage = 0.0
        # Source tracking for stickyness (preserving phrases)
        self.source_file = source_file
        self.chunk_index = chunk_index

    def _apply_window(self, audio):
        """Apply windowing function to reduce spectral leakage."""
        if self.window_type == 'none' or len(audio) == 0:
            return audio

        # Create window of same length as audio
        if self.window_type == 'hann':
            window = signal.windows.hann(len(audio))
        elif self.window_type == 'hamming':
            window = signal.windows.hamming(len(audio))
        elif self.window_type == 'blackman':
            window = signal.windows.blackman(len(audio))
        elif self.window_type == 'bartlett':
            window = signal.windows.bartlett(len(audio))
        else:
            # Default to hann if unknown
            window = signal.windows.hann(len(audio))

        return audio * window

    def _extract_features(self):
        """Calculates the acoustic features (fingerprint) of the chunk."""
        hop_length = 512

        # Apply windowing to reduce spectral leakage
        windowed_audio = self._apply_window(self.audio)

        # 1. Loudness (RMS Energy)
        rms = librosa.feature.rms(y=windowed_audio, hop_length=hop_length)
        avg_rms = np.mean(rms)
        # Store the full RMS envelope for envelope matching
        rms_envelope = rms[0]  # Remove the extra dimension

        # 2. Pitch (Fundamental Frequency)
        pitches, _, _ = librosa.pyin(
            y=windowed_audio,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=self.sr
        )
        avg_pitch = np.nanmean(pitches) if not np.all(np.isnan(pitches)) else 0.0

        # 3. Timbre (MFCCs)
        mfccs = librosa.feature.mfcc(
            y=windowed_audio,
            sr=self.sr,
            n_mfcc=13,
            hop_length=hop_length
        )
        avg_mfccs = np.mean(mfccs, axis=1)

        return {
            'rms': float(avg_rms),
            'pitch': float(avg_pitch),
            'mfccs': avg_mfccs,
            'duration': float(len(self.audio)),
            'rms_envelope': rms_envelope  # Store the envelope
        }

# --- Cache Management Functions ---

def compute_path_hash(filepath):
    """Compute a hash of the filepath string to use as cache key."""
    return hashlib.md5(os.path.abspath(filepath).encode('utf-8')).hexdigest()

def compute_file_hash(filepath):
    """Compute a hash of the file content to detect changes."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error computing file hash for {filepath}: {e}")
        return None

def get_cache_paths(filepath, chunk_duration_min_s, chunk_duration_max_s, overlap, sample_rate, window_type, cache_dir=".mosaic-cache"):
    """Get the cache file paths for a given audio file and chunking parameters."""
    path_hash = compute_path_hash(filepath)
    # Include chunking parameters in cache key
    params_str = f"{chunk_duration_min_s}_{chunk_duration_max_s}_{overlap}_{sample_rate}_{window_type}"
    params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()[:8]
    chunks_file = os.path.join(cache_dir, f"{path_hash}_{params_hash}_chunks.pkl")
    hash_file = os.path.join(cache_dir, f"{path_hash}_{params_hash}_hash.txt")
    return chunks_file, hash_file

def load_chunks_from_cache(filepath, chunk_duration_min_s, chunk_duration_max_s, overlap, sample_rate, window_type, cache_dir=".mosaic-cache"):
    """
    Load cached chunks if they exist and are valid.
    Returns (chunks, cache_hit) where cache_hit is True if cache was used.
    """
    chunks_file, hash_file = get_cache_paths(filepath, chunk_duration_min_s, chunk_duration_max_s, overlap, sample_rate, window_type, cache_dir)

    # Check if cache files exist
    if not os.path.exists(chunks_file) or not os.path.exists(hash_file):
        return None, False

    # Read the stored file hash
    try:
        with open(hash_file, 'r') as f:
            stored_hash = f.read().strip()
    except Exception as e:
        print(f"Error reading cache hash file: {e}")
        return None, False

    # Compute current file hash
    current_hash = compute_file_hash(filepath)
    if current_hash is None:
        return None, False

    # Check if hashes match
    if stored_hash != current_hash:
        print(f"Cache invalidated for {filepath} (file content changed)")
        return None, False

    # Load cached chunks
    try:
        with open(chunks_file, 'rb') as f:
            chunks = pickle.load(f)
        print(f"Loaded {len(chunks)} chunks from cache for {filepath}")
        return chunks, True
    except Exception as e:
        print(f"Error loading cached chunks: {e}")
        return None, False

def save_chunks_to_cache(filepath, chunks, chunk_duration_min_s, chunk_duration_max_s, overlap, sample_rate, window_type, cache_dir=".mosaic-cache"):
    """Save chunks to cache along with file hash."""
    # Create cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)

    chunks_file, hash_file = get_cache_paths(filepath, chunk_duration_min_s, chunk_duration_max_s, overlap, sample_rate, window_type, cache_dir)

    # Compute and save file hash
    file_hash = compute_file_hash(filepath)
    if file_hash is None:
        return

    try:
        with open(hash_file, 'w') as f:
            f.write(file_hash)
    except Exception as e:
        print(f"Error saving cache hash: {e}")
        return

    # Save chunks
    try:
        with open(chunks_file, 'wb') as f:
            pickle.dump(chunks, f)
        print(f"Cached {len(chunks)} chunks for {filepath}")
    except Exception as e:
        print(f"Error saving chunks to cache: {e}")

# --- Core Functions ---

def analyze_file(filepath, chunk_duration_min_s, chunk_duration_max_s, overlap, sample_rate, window_type='hann'):
    """
    Loads an audio file and splits it into variable-sized AudioChunk objects.

    Args:
        filepath: Path to audio file
        chunk_duration_min_s: Minimum chunk duration in seconds
        chunk_duration_max_s: Maximum chunk duration in seconds
        overlap: Overlap fraction (0.0 = no overlap, 0.5 = 50% overlap)
        sample_rate: Target sample rate
        window_type: Window function type ('hann', 'hamming', 'blackman', 'bartlett', 'none')
    """
    print(f"Analyzing file: {filepath}...")

    # Try to load from cache first
    cached_chunks, cache_hit = load_chunks_from_cache(filepath, chunk_duration_min_s, chunk_duration_max_s, overlap, sample_rate, window_type)
    if cache_hit and cached_chunks is not None:
        return cached_chunks

    try:
        y, sr = librosa.load(filepath, sr=sample_rate)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []

    chunks = []
    current_pos_samples = 0
    y_len_samples = len(y)

    min_chunk_samples = int(chunk_duration_min_s * sr)
    if min_chunk_samples == 0:
        print("Error: Minimum chunk size is too small. Please use a larger --chunk-size-min.")
        return []

    last_update_pos = 0
    with tqdm(total=y_len_samples, desc=f"Chunking {filepath.split('/')[-1]}") as pbar:
        while current_pos_samples < y_len_samples:
            chunk_duration_s = np.random.uniform(chunk_duration_min_s, chunk_duration_max_s)
            chunk_samples = int(chunk_duration_s * sr)

            start = current_pos_samples
            end = start + chunk_samples

            if end >= y_len_samples:
                end = y_len_samples

            chunk_audio = y[start:end]
            actual_chunk_len = len(chunk_audio)

            if actual_chunk_len >= min_chunk_samples:
                chunk_idx = len(chunks)
                chunks.append(AudioChunk(chunk_audio, sr, window_type, filepath, chunk_idx))

            # Update progress bar with actual advancement (not chunk size)
            advancement = current_pos_samples - last_update_pos
            if advancement > 0:
                pbar.update(advancement)
                last_update_pos = current_pos_samples

            # Advance position with overlap
            # overlap = 0.5 means 50% overlap, so advance by 50% of chunk size
            hop_samples = int(chunk_samples * (1 - overlap))
            if hop_samples == 0:
                hop_samples = 1  # Ensure we always make progress
            current_pos_samples += hop_samples

    # Save to cache for next time
    save_chunks_to_cache(filepath, chunks, chunk_duration_min_s, chunk_duration_max_s, overlap, sample_rate, window_type)

    return chunks

def deplete_usage(chunks, decay_rate=0.99):
    """
    Decay usage values for all chunks to allow reuse over time.

    Args:
        chunks: List of AudioChunk objects
        decay_rate: Multiplicative decay factor (0.99 = 1% decay per call)
    """
    for chunk in chunks:
        # Handle chunks loaded from old cache that don't have usage attribute
        if not hasattr(chunk, 'usage'):
            chunk.usage = 0.0
        chunk.usage *= decay_rate

def calculate_chunk_distance(ref_chunk, src_chunk, feature_weights, use_duration_match, mfcc_distance_metric, usage_importance=0.0):
    """
    Calculate the distance between two chunks.

    Args:
        ref_chunk: Reference chunk
        src_chunk: Source chunk to compare
        feature_weights: Dictionary of feature weights
        use_duration_match: Whether to match duration
        mfcc_distance_metric: 'euclidean' or 'cosine'
        usage_importance: Weight for usage/novelty

    Returns:
        Distance value (lower is better match)
    """
    # Unpack weights
    w_rms = feature_weights['rms']
    w_pitch = feature_weights['pitch']
    w_mfcc = feature_weights['mfcc']
    w_duration = feature_weights.get('duration', 0.0)

    # Normalized features
    ref_rms = ref_chunk.norm_features['rms']
    ref_pitch = ref_chunk.norm_features['pitch']
    ref_mfccs = ref_chunk.norm_features['mfccs']
    ref_duration = ref_chunk.norm_features['duration']

    src_rms = src_chunk.norm_features['rms']
    src_pitch = src_chunk.norm_features['pitch']
    src_mfccs = src_chunk.norm_features['mfccs']
    src_duration = src_chunk.norm_features['duration']

    # Calculate distances
    dist_rms = abs(ref_rms - src_rms)
    dist_pitch = abs(ref_pitch - src_pitch)

    # MFCC distance
    if mfcc_distance_metric == 'euclidean':
        dist_mfcc = np.linalg.norm(ref_mfccs - src_mfccs)
    elif mfcc_distance_metric == 'cosine':
        norm_ref = np.linalg.norm(ref_mfccs)
        norm_src = np.linalg.norm(src_mfccs)
        if norm_ref == 0 or norm_src == 0:
            dist_mfcc = 1.0
        else:
            cosine_sim = np.dot(ref_mfccs, src_mfccs) / (norm_ref * norm_src)
            dist_mfcc = 1 - cosine_sim
    else:
        raise ValueError(f"Unknown MFCC distance metric: {mfcc_distance_metric}")

    # Total weighted distance (acoustic similarity)
    total_distance = (w_rms * dist_rms) + (w_pitch * dist_pitch) + (w_mfcc * dist_mfcc)

    if use_duration_match:
        dist_duration = abs(ref_duration - src_duration)
        total_distance += (w_duration * dist_duration)

    # Blend in usage to penalize overused blocks (novelty)
    if usage_importance > 0:
        # Handle chunks loaded from old cache that don't have usage attribute
        if not hasattr(src_chunk, 'usage'):
            src_chunk.usage = 0.0
        total_distance = (1 - usage_importance) * total_distance + usage_importance * src_chunk.usage

    return total_distance

def find_best_match(reference_chunk, source_pool, feature_weights, use_duration_match, mfcc_distance_metric, usage_importance=0.0, last_chunk=None, stickyness=0.0):
    """
    Finds the best matching chunk from the source_pool for a given reference_chunk.

    Args:
        reference_chunk: The target chunk to match
        source_pool: List of source chunks to search
        feature_weights: Dictionary of feature weights
        use_duration_match: Whether to match duration
        mfcc_distance_metric: 'euclidean' or 'cosine'
        usage_importance: Weight for usage/novelty (0.0 = ignore usage, higher = prefer unused blocks)
        last_chunk: Previously used chunk (for stickyness)
        stickyness: Preference for sequential blocks (0.0 = disabled, higher = prefer continuation)
    """
    best_match = None
    min_distance = float('inf')

    # Find the best match from the source pool
    for source_chunk in source_pool:
        distance = calculate_chunk_distance(
            reference_chunk, source_chunk, feature_weights,
            use_duration_match, mfcc_distance_metric, usage_importance
        )

        if distance < min_distance:
            min_distance = distance
            best_match = source_chunk

    # Apply stickyness: check if we should use the next sequential block instead
    if stickyness > 0 and last_chunk is not None and best_match is not None:
        # Handle chunks loaded from old cache that don't have source_file/chunk_index
        if not hasattr(last_chunk, 'source_file'):
            return best_match
        if not hasattr(last_chunk, 'chunk_index'):
            return best_match

        # Find the next sequential chunk from the same source file
        next_chunk = None
        for chunk in source_pool:
            if not hasattr(chunk, 'source_file') or not hasattr(chunk, 'chunk_index'):
                continue
            if (chunk.source_file == last_chunk.source_file and
                chunk.chunk_index == last_chunk.chunk_index + 1):
                next_chunk = chunk
                break

        # If we found a next chunk, compare it
        if next_chunk is not None:
            dist_to_next = calculate_chunk_distance(
                reference_chunk, next_chunk, feature_weights,
                use_duration_match, mfcc_distance_metric, usage_importance
            )

            # Stickyness formula from Samplebrain:
            # If dist_to_next * (1 - stickyness) < best_dist * stickyness, use next chunk
            # This means higher stickyness favors sequential blocks
            if dist_to_next * (1 - stickyness) < min_distance * stickyness:
                return next_chunk

    return best_match

def normalize_features(all_chunks):
    """
    Normalizes features across all chunks to a [0, 1] range.
    """
    print("Normalizing features...")
    all_rms = [c.features['rms'] for c in all_chunks]
    all_pitches = [c.features['pitch'] for c in all_chunks]
    all_durations = [c.features['duration'] for c in all_chunks]

    # Min-max normalization
    min_rms, max_rms = min(all_rms), max(all_rms)
    min_pitch, max_pitch = min(all_pitches), max(all_pitches)
    min_duration, max_duration = min(all_durations), max(all_durations)

    # For MFCCs
    all_mfccs = np.array([c.features['mfccs'] for c in all_chunks])
    min_mfccs = np.min(all_mfccs, axis=0)
    max_mfccs = np.max(all_mfccs, axis=0)

    for chunk in tqdm(all_chunks, desc="Applying normalization"):
        norm_rms = (chunk.features['rms'] - min_rms) / (max_rms - min_rms) if (max_rms - min_rms) != 0 else 0.5
        norm_pitch = (chunk.features['pitch'] - min_pitch) / (max_pitch - min_pitch) if (max_pitch - min_pitch) != 0 else 0.5
        norm_duration = (chunk.features['duration'] - min_duration) / (max_duration - min_duration) if (max_duration - min_duration) != 0 else 0.5
        norm_mfccs = (chunk.features['mfccs'] - min_mfccs) / (max_mfccs - min_mfccs + 1e-9)

        chunk.norm_features = {
            'rms': norm_rms,
            'pitch': norm_pitch,
            'mfccs': norm_mfccs,
            'duration': norm_duration
        }

def apply_pitch_tuning(source_chunk, ref_pitch_hz):
    """
    Applies pitch shifting to match the reference pitch.
    Returns a new AudioChunk with pitch-shifted audio.
    """
    src_pitch_hz = source_chunk.features['pitch']

    # Only shift if both pitches are valid
    if ref_pitch_hz > 0 and src_pitch_hz > 0:
        # Calculate pitch difference in semitones
        n_semitones = 12 * np.log2(ref_pitch_hz / src_pitch_hz)

        # Create a deep copy to avoid modifying the original
        tuned_chunk = copy.deepcopy(source_chunk)

        # Apply pitch shifting
        tuned_chunk.audio = librosa.effects.pitch_shift(
            y=tuned_chunk.audio,
            sr=tuned_chunk.sr,
            n_steps=n_semitones
        )
        return tuned_chunk

    return source_chunk

def apply_volume_tuning(source_chunk, ref_rms):
    """
    Scales the overall volume to match the reference RMS.
    Returns a new AudioChunk with volume-adjusted audio.
    """
    src_rms = source_chunk.features['rms']

    # Avoid division by zero
    if src_rms > 1e-6:
        # Calculate scaling factor
        scale_factor = ref_rms / src_rms

        # Create a copy and scale the audio
        tuned_chunk = copy.deepcopy(source_chunk)
        tuned_chunk.audio = tuned_chunk.audio * scale_factor

        return tuned_chunk

    return source_chunk

def apply_envelope_tuning(source_chunk, ref_envelope, hop_length=512):
    """
    Applies the reference chunk's volume envelope to the source chunk.

    This works by:
    1. Extracting the RMS envelope from both chunks
    2. Interpolating the reference envelope to match the source chunk's length
    3. Creating a gain curve that transforms the source envelope to match the reference
    4. Applying this gain curve to the source audio

    Returns a new AudioChunk with envelope-matched audio.
    """
    # Get the reference envelope
    ref_env = ref_envelope

    # Get the source envelope
    src_env = source_chunk.features['rms_envelope']

    # If either envelope is too short or invalid, skip envelope matching
    if len(ref_env) < 2 or len(src_env) < 2:
        return source_chunk

    # Interpolate reference envelope to match source chunk length in samples
    source_audio_len = len(source_chunk.audio)

    # Create time arrays for interpolation (in samples)
    ref_time = np.linspace(0, source_audio_len - 1, len(ref_env))
    src_time = np.linspace(0, source_audio_len - 1, len(src_env))

    # Interpolate both envelopes to audio sample rate
    try:
        ref_interp = interp1d(ref_time, ref_env, kind='linear', fill_value='extrapolate')
        src_interp = interp1d(src_time, src_env, kind='linear', fill_value='extrapolate')

        sample_indices = np.arange(source_audio_len)
        ref_env_full = ref_interp(sample_indices)
        src_env_full = src_interp(sample_indices)

        # Calculate gain curve (avoid division by zero)
        gain_curve = np.where(src_env_full > 1e-6, ref_env_full / src_env_full, 1.0)

        # Smooth the gain curve to avoid artifacts
        # Use a simple moving average with window size proportional to hop_length
        window_size = min(hop_length * 2, len(gain_curve) // 4)
        if window_size > 1:
            kernel = np.ones(window_size) / window_size
            gain_curve = np.convolve(gain_curve, kernel, mode='same')

        # Clamp extreme gain values to avoid distortion
        gain_curve = np.clip(gain_curve, 0.1, 10.0)

        # Create a copy and apply the gain curve
        tuned_chunk = copy.deepcopy(source_chunk)
        tuned_chunk.audio = tuned_chunk.audio * gain_curve

        return tuned_chunk

    except Exception as e:
        # If interpolation fails, return the original chunk
        print(f"Warning: Envelope tuning failed: {e}")
        return source_chunk

def concatenate_with_crossfade(chunks, fade_duration_s, sample_rate):
    """Concatenates a list of audio chunks with a linear crossfade."""
    if not chunks:
        return np.array([])
    if len(chunks) == 1:
        return chunks[0].audio

    print("Concatenating chunks with crossfade...")
    fade_samples = int(fade_duration_s * sample_rate)

    output = chunks[0].audio.copy()

    for i in tqdm(range(1, len(chunks)), desc="Crossfading"):
        next_chunk_audio = chunks[i].audio

        overlap_len = min(fade_samples, len(output), len(next_chunk_audio))

        if overlap_len == 0:
            output = np.concatenate((output, next_chunk_audio))
            continue

        # Create fade ramps
        fade_out = np.linspace(1, 0, overlap_len)
        fade_in = np.linspace(0, 1, overlap_len)

        # Crossfaded section
        crossfaded_section = (output[-overlap_len:] * fade_out) + (next_chunk_audio[:overlap_len] * fade_in)

        # Concatenate
        output = np.concatenate((output[:-overlap_len], crossfaded_section, next_chunk_audio[overlap_len:]))

    return output

# --- Main Execution Block ---
def main():
    parser = argparse.ArgumentParser(
        description="Enhanced audio mosaicing with pitch and volume tuning."
    )
    parser.add_argument('-r', '--reference', type=str, required=True,
                       help="Path to the reference audio file.")
    parser.add_argument('-s', '--sources', nargs='+', required=True,
                       help="Paths to one or more source audio files.")
    parser.add_argument('-o', '--output', type=str, required=True,
                       help="Path for the output audio file.")
    parser.add_argument('--chunk-size-min', type=float, default=0.1,
                       help="Minimum duration of each chunk in seconds. Default: 0.1")
    parser.add_argument('--chunk-size-max', type=float, default=0.4,
                       help="Maximum duration of each chunk in seconds. Default: 0.4")
    parser.add_argument('--overlap', type=float, default=0.5,
                       help="Chunk overlap fraction (0.0 = no overlap, 0.5 = 50%% overlap). Default: 0.5")
    parser.add_argument('--window', type=str, default='hann',
                       choices=['hann', 'hamming', 'blackman', 'bartlett', 'none'],
                       help="Window function for FFT analysis. Default: 'hann'")
    parser.add_argument('--no-crossfade', dest='crossfade', action='store_false',
                       help="Disable crossfading between chunks.")
    parser.add_argument('--mfcc-distance-metric', type=str,
                       choices=['euclidean', 'cosine'], default='euclidean',
                       help="Distance metric for MFCCs. Default: 'euclidean'.")
    parser.add_argument('--weight-rms', type=float, default=1.0,
                       help="Weight for RMS (loudness) matching. Default: 1.0")
    parser.add_argument('--weight-pitch', type=float, default=1.5,
                       help="Weight for pitch matching. Default: 1.5")
    parser.add_argument('--weight-mfcc', type=float, default=1.0,
                       help="Weight for MFCC (timbre) matching. Default: 1.0")
    parser.add_argument('--weight-duration', type=float, default=0.5,
                       help="Weight for duration matching. Default: 0.5")
    parser.add_argument('--usage-importance', type=float, default=0.0,
                       help="Weight for usage/novelty (0.0 = ignore, higher = prefer unused blocks). Default: 0.0")
    parser.add_argument('--stickyness', type=float, default=0.0,
                       help="Preference for sequential blocks from same source (0.0 = disabled, higher = preserve phrases). Default: 0.0")
    parser.add_argument('--crossfade-duration', type=float, default=0.01,
                       help="Duration of the crossfade in seconds. Default: 0.01")
    parser.add_argument('--no-chunk-duration-match', dest='duration_match',
                       action='store_false',
                       help="Disable matching based on chunk duration.")
    parser.add_argument('--sr', type=int, default=22050,
                       help="Sample rate to use for all processing.")

    # NEW TUNING OPTIONS
    parser.add_argument('--enable-pitch-tuning', action='store_true',
                       help="Enable pitch shifting to match reference pitch.")
    parser.add_argument('--enable-volume-tuning', action='store_true',
                       help="Enable volume scaling to match reference RMS.")
    parser.add_argument('--enable-envelope-tuning', action='store_true',
                       help="Enable volume envelope matching for dynamic expression.")
    parser.add_argument('--enable-all-tuning', action='store_true',
                       help="Enable all tuning options (pitch, volume, envelope).")

    args = parser.parse_args()

    # If --enable-all-tuning is set, enable all tuning options
    if args.enable_all_tuning:
        args.enable_pitch_tuning = True
        args.enable_volume_tuning = True
        args.enable_envelope_tuning = True

    # Validate chunk sizes
    if args.chunk_size_min >= args.chunk_size_max:
        print("Error: --chunk-size-min must be smaller than --chunk-size-max.")
        return
    if args.chunk_size_min <= 0:
        print("Error: --chunk-size-min must be positive.")
        return
    if not 0.0 <= args.overlap < 1.0:
        print("Error: --overlap must be in range [0.0, 1.0).")
        return

    # --- 1. Analysis Phase ---
    reference_chunks = analyze_file(args.reference, args.chunk_size_min,
                                    args.chunk_size_max, args.overlap, args.sr, args.window)
    if not reference_chunks:
        print("Could not process reference file. Exiting.")
        return

    source_pool = []
    for source_file in args.sources:
        source_pool.extend(analyze_file(source_file, args.chunk_size_min,
                                       args.chunk_size_max, args.overlap, args.sr, args.window))

    if not source_pool:
        print("Could not process any source files. Exiting.")
        return

    # --- 2. Normalization ---
    all_chunks_for_norm = reference_chunks + source_pool
    normalize_features(all_chunks_for_norm)

    # --- 3. Matching and Tuning Phase ---
    print("Finding best matches and applying tuning...")
    output_chunks = []
    last_used_chunk = None

    feature_weights = {
        'rms': args.weight_rms,
        'pitch': args.weight_pitch,
        'mfcc': args.weight_mfcc,
        'duration': args.weight_duration
    }

    for idx, ref_chunk in enumerate(tqdm(reference_chunks, desc="Matching and tuning")):
        # Periodically decay usage values to allow reuse
        if idx % 10 == 0:
            deplete_usage(source_pool, decay_rate=0.99)

        # Find the best match (with stickyness support)
        best_source_chunk = find_best_match(
            ref_chunk, source_pool, feature_weights,
            args.duration_match, args.mfcc_distance_metric,
            usage_importance=args.usage_importance,
            last_chunk=last_used_chunk,
            stickyness=args.stickyness
        )

        if best_source_chunk:
            # Increase usage of chosen chunk to encourage variety
            # Handle chunks loaded from old cache that don't have usage attribute
            if not hasattr(best_source_chunk, 'usage'):
                best_source_chunk.usage = 0.0
            best_source_chunk.usage += 1.0

            # Track this chunk for stickyness
            last_used_chunk = best_source_chunk

            chunk_to_add = best_source_chunk

            # Apply tuning in order: pitch -> volume -> envelope
            # This order matters because envelope matching works best after volume normalization

            if args.enable_pitch_tuning:
                ref_pitch_hz = ref_chunk.features['pitch']
                chunk_to_add = apply_pitch_tuning(chunk_to_add, ref_pitch_hz)

            if args.enable_volume_tuning:
                ref_rms = ref_chunk.features['rms']
                chunk_to_add = apply_volume_tuning(chunk_to_add, ref_rms)

            if args.enable_envelope_tuning:
                ref_envelope = ref_chunk.features['rms_envelope']
                chunk_to_add = apply_envelope_tuning(chunk_to_add, ref_envelope)

            output_chunks.append(chunk_to_add)

    # --- 4. Synthesis Phase ---
    if args.crossfade:
        final_audio = concatenate_with_crossfade(output_chunks,
                                                 args.crossfade_duration, args.sr)
    else:
        print("Synthesizing output file (no crossfade)...")
        final_audio = np.concatenate([chunk.audio for chunk in output_chunks])

    # Write the final audio
    try:
        sf.write(args.output, final_audio, args.sr)
        print(f"\nSuccess! Output saved to: {args.output}")

        # Print which tuning options were used
        tuning_used = []
        if args.enable_pitch_tuning:
            tuning_used.append("pitch")
        if args.enable_volume_tuning:
            tuning_used.append("volume")
        if args.enable_envelope_tuning:
            tuning_used.append("envelope")

        if tuning_used:
            print(f"Tuning applied: {', '.join(tuning_used)}")
        else:
            print("No tuning applied (use --enable-all-tuning or individual flags)")

    except Exception as e:
        print(f"Error writing output file: {e}")

# =============================================================================
# FUTURE ENHANCEMENT IMPLEMENTATION GUIDE
# =============================================================================
#
# Two additional features from Samplebrain remain unimplemented. Below is a
# detailed guide for implementing them if needed in the future.
#
# -----------------------------------------------------------------------------
# 1. DUAL PROCESSING (Normal + Normalized)
# -----------------------------------------------------------------------------
#
# CONCEPT:
# Analyze each chunk twice - once with original dynamics, once normalized.
# This allows blending between "frequency-only matching" and "frequency+dynamics".
#
# WHEN TO IMPLEMENT:
# - When users want control over whether to preserve source dynamics
# - When matching purely on timbre regardless of volume differences
# - When you want Samplebrain's "freq & dynamics" slider behavior
#
# COMPLEXITY ADDED:
# - Memory: Doubles feature storage (2x FFT, 2x MFCC per chunk)
# - CPU: Doubles analysis time (2x FFT/MFCC computation)
# - Code: ~100 lines of additional feature extraction
# - UI: New parameter --dynamics-ratio (0.0=ignore dynamics, 1.0=include dynamics)
#
# IMPLEMENTATION STEPS:
#
# 1. Modify AudioChunk._extract_features():
#    - Add second analysis pass with normalized audio
#    - Store as 'm_n_fft', 'm_n_mfcc' (normalized versions)
#    - Current code would become 'm_fft', 'm_mfcc' (normal versions)
#
#    Example:
#    ```python
#    # Normal version (current)
#    self.m_fft = compute_fft(windowed_audio)
#    self.m_mfcc = compute_mfcc(windowed_audio)
#
#    # Normalized version (new)
#    normalized_audio = windowed_audio / (np.max(np.abs(windowed_audio)) + 1e-9)
#    self.m_n_fft = compute_fft(normalized_audio)
#    self.m_n_mfcc = compute_mfcc(normalized_audio)
#    ```
#
# 2. Modify calculate_chunk_distance():
#    - Calculate distance for both normal and normalized
#    - Blend based on dynamics_ratio parameter:
#      `final_dist = blend(normal_dist, normalized_dist, dynamics_ratio)`
#
# 3. Add command-line argument:
#    ```python
#    parser.add_argument('--dynamics-ratio', type=float, default=1.0,
#                       help="Blend normal/normalized (0.0=ignore dynamics, 1.0=include)")
#    ```
#
# 4. Update cache key to include dynamics_ratio
#
# PERFORMANCE IMPACT:
# - Analysis: 2x slower (need to process twice)
# - Memory: 2x chunk storage
# - Matching: Negligible (just blending two distances)
#
# -----------------------------------------------------------------------------
# 2. SYNAPTIC SEARCH NETWORK
# -----------------------------------------------------------------------------
#
# CONCEPT:
# Pre-compute a similarity graph where each chunk stores indices of its 1000
# nearest neighbors. Search only these neighbors instead of entire pool.
#
# WHEN TO IMPLEMENT:
# - When source pool exceeds 10,000 chunks (hours of audio)
# - When real-time performance is critical
# - When you can afford O(n²) preprocessing time
#
# COMPLEXITY ADDED:
# - Memory: ~4KB per chunk for 1000 neighbor indices = 40MB for 10k chunks
# - CPU: O(n²) preprocessing (can take 10+ minutes for large sets)
# - Code: ~300 lines for network building, modified search
# - Algorithmic: Complex data structure management
#
# IMPLEMENTATION STEPS:
#
# 1. Add synapse storage to AudioChunk:
#    ```python
#    class AudioChunk:
#        def __init__(self, ...):
#            ...
#            self.synapses = []  # List of indices to similar chunks
#    ```
#
# 2. Implement build_synapses_network():
#    ```python
#    def build_synapses_network(source_pool, num_synapses=1000):
#        """Build similarity network for all chunks."""
#        print("Building synaptic network (this may take several minutes)...")
#        for i, chunk_a in enumerate(tqdm(source_pool)):
#            distances = []
#            for j, chunk_b in enumerate(source_pool):
#                if i == j:
#                    continue
#                dist = calculate_chunk_distance(chunk_a, chunk_b, ...)
#                distances.append((dist, j))
#
#            # Sort and keep top N
#            distances.sort()
#            chunk_a.synapses = [idx for _, idx in distances[:num_synapses]]
#    ```
#
# 3. Implement synaptic search:
#    ```python
#    def find_best_match_synaptic(ref_chunk, source_pool, last_chunk, ...):
#        """Search only synaptic connections of last chunk."""
#        if last_chunk is None:
#            # First iteration - search all
#            return find_best_match(ref_chunk, source_pool, ...)
#
#        # Search only synaptically connected chunks
#        candidates = [source_pool[idx] for idx in last_chunk.synapses]
#        return find_best_match(ref_chunk, candidates, ...)
#    ```
#
# 4. Add command-line arguments:
#    ```python
#    parser.add_argument('--use-synaptic-search', action='store_true',
#                       help="Use synaptic network for faster search")
#    parser.add_argument('--num-synapses', type=int, default=1000,
#                       help="Number of connections per chunk")
#    ```
#
# 5. Call build_synapses_network() after normalization, before matching
#
# PERFORMANCE IMPACT:
# - Preprocessing: O(n²) - very slow for large n
# - Search: O(1) instead of O(n) - huge speedup
# - Memory: Minimal (~4KB per chunk for indices)
#
# WHEN TO SKIP:
# - Current implementation handles <10,000 chunks efficiently
# - Linear search is fast enough for typical use cases
# - Avoids preprocessing time and complexity
#
# =============================================================================

if __name__ == '__main__':
    main()
