#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Audio Mosaicing and Concatenative Synthesis Script

This script reconstructs a reference audio file using small chunks from a set of
source audio files. It works by analyzing the acoustic properties of the 
reference file's segments and finding the best-matching segments from the 
source files.

Core Concepts:
- Chunking: The source and reference files are split into small audio segments
  (chunks).
- Feature Extraction: For each chunk, we calculate a "fingerprint" based on
  its acoustic properties:
    - Loudness: The overall volume, measured by Root Mean Square (RMS) energy.
    - Pitch: The fundamental frequency of the sound, which we perceive as how
      high or low the sound is.
    - Timbre: The "color" or quality of the sound. This is what distinguishes
      a piano from a voice playing the same note at the same loudness. We use
      Mel-Frequency Cepstral Coefficients (MFCCs) for this, which is the
      industry standard for timbre representation.
- Matching: For each chunk in the reference file, the script searches all
  source chunks to find the one with the most similar fingerprint. This is
  done by calculating a "distance" in the feature space.
- Concatenation: The best-matching source chunks are stitched together in
  order to create the final output audio.

Dependencies:
You will need to install the following Python libraries:
pip install numpy librosa soundfile tqdm

Usage:
Save the script as "mosaic.py" and run it from your terminal.

python mosaic.py \
    --reference path/to/your/reference.wav \
    --sources path/to/source1.wav path/to/source2.wav \
    --output path/to/your/output.wav \
    --chunk-size-min 0.1 \ # Minimum duration of a chunk
    --chunk-size-max 0.4 \ # Maximum duration of a chunk
    --mfcc-distance-metric cosine \ # Use cosine similarity for timbre matching
    --weight-rms 1.0 \ # Weight for loudness matching
    --weight-pitch 1.5 \ # Weight for pitch matching
    --weight-mfcc 2.0 \ # Weight for timbre matching (increased for cosine)
    --adjust-pitch # Enable autotune-like pitch correction

"""

import argparse
import numpy as np
import librosa
import soundfile as sf
from tqdm import tqdm
import warnings
import copy

# Suppress annoying librosa warnings about audioread
warnings.filterwarnings('ignore', category=UserWarning)

# --- Data Structure for an Audio Chunk ---
class AudioChunk:
    """A simple class to hold a chunk of audio and its features."""
    def __init__(self, audio_data, sample_rate):
        self.audio = audio_data
        self.sr = sample_rate
        self.features = self._extract_features()
        # We will add the normalized features later as an attribute
        self.norm_features = {}

    def _extract_features(self):
        """Calculates the acoustic features (fingerprint) of the chunk."""
        # Use a small hop_length for better temporal resolution in feature extraction
        hop_length = 512

        # 1. Loudness (RMS Energy)
        # We take the mean of the RMS values across the chunk.
        rms = librosa.feature.rms(y=self.audio, hop_length=hop_length)
        avg_rms = np.mean(rms)

        # 2. Pitch (Fundamental Frequency)
        # We use the PYIN algorithm to estimate pitch.
        pitches, _, _ = librosa.pyin(y=self.audio, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=self.sr)
        # Average only the valid (non-NaN) pitch values.
        avg_pitch = np.nanmean(pitches) if not np.all(np.isnan(pitches)) else 0.0

        # 3. Timbre (MFCCs)
        # We get a vector of MFCCs and take the mean across the chunk.
        mfccs = librosa.feature.mfcc(y=self.audio, sr=self.sr, n_mfcc=13, hop_length=hop_length)
        avg_mfccs = np.mean(mfccs, axis=1)

        return {
            'rms': float(avg_rms),
            'pitch': float(avg_pitch),
            'mfccs': avg_mfccs,
            'duration': float(len(self.audio))
        }

# --- Core Functions ---

def analyze_file(filepath, chunk_duration_min_s, chunk_duration_max_s, sample_rate):
    """Loads an audio file and splits it into variable-sized AudioChunk objects."""
    print(f"Analyzing file: {filepath}...")
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
        print("Error: Minimum chunk size is too small, resulting in zero samples. Please use a larger value for --chunk-size-min.")
        return []

    with tqdm(total=y_len_samples, desc=f"Chunking {filepath.split('/')[-1]}") as pbar:
        while current_pos_samples < y_len_samples:
            # Randomly determine chunk duration for this chunk
            chunk_duration_s = np.random.uniform(chunk_duration_min_s, chunk_duration_max_s)
            chunk_samples = int(chunk_duration_s * sr)

            start = current_pos_samples
            end = start + chunk_samples

            # For the last chunk, just take what's left
            if end >= y_len_samples:
                end = y_len_samples

            chunk_audio = y[start:end]
            actual_chunk_len = len(chunk_audio)

            # Ensure the chunk is not empty and is of a minimum reasonable size
            # to avoid issues with feature extraction on tiny slivers of audio.
            if actual_chunk_len >= min_chunk_samples:
                chunks.append(AudioChunk(chunk_audio, sr))

            pbar.update(actual_chunk_len)
            current_pos_samples = end
            
    return chunks

def find_best_match(reference_chunk, source_pool, feature_weights, use_duration_match, mfcc_distance_metric):
    """
    Finds the best matching chunk from the source_pool for a given reference_chunk.
    
    The "best" match is the one with the smallest weighted distance in the
    feature space. Duration can be optionally included in this calculation.
    """
    best_match = None
    min_distance = float('inf')

    # Unpack weights
    w_rms, w_pitch, w_mfcc = feature_weights['rms'], feature_weights['pitch'], feature_weights['mfcc']
    w_duration = feature_weights.get('duration', 0.0)

    # Normalized features from the reference chunk
    ref_rms = reference_chunk.norm_features['rms']
    ref_pitch = reference_chunk.norm_features['pitch']
    ref_mfccs = reference_chunk.norm_features['mfccs']
    ref_duration = reference_chunk.norm_features['duration']

    for source_chunk in source_pool:
        # Normalized features from the source chunk
        src_rms = source_chunk.norm_features['rms']
        src_pitch = source_chunk.norm_features['pitch']
        src_mfccs = source_chunk.norm_features['mfccs']
        src_duration = source_chunk.norm_features['duration']

        # --- Feature Distance Calculation ---
        # Calculate distance for scalar features (lower is better)
        dist_rms = abs(ref_rms - src_rms)
        dist_pitch = abs(ref_pitch - src_pitch)
        
        # --- MFCC (Timbre) Distance Calculation ---
        # This block calculates the distance between the timbre of the reference
        # and source chunks using the selected metric.
        #
        # HOW TO ADD A NEW METRIC:
        # 1. Add a new `elif mfcc_distance_metric == 'your_metric_name':` block.
        # 2. Implement your distance calculation. The result (`dist_mfcc`) should be
        #    a single float where 0 means a perfect match and higher values mean a
        #    worse match.
        # 3. If you are implementing a SIMILARITY metric (where higher is better, e.g.,
        #    ranging from 0 to 1), you must convert it to a DISTANCE metric. A common
        #    way is `distance = 1 - similarity`.
        # 4. Add 'your_metric_name' to the `choices` list in the `add_argument` call
        #    for `--mfcc-distance-metric` in the `main` function.
        
        if mfcc_distance_metric == 'euclidean':
            # Euclidean distance (L2 norm): Measures the straight-line distance
            # between the two MFCC vectors in multi-dimensional space.
            # It is sensitive to both magnitude and angle.
            dist_mfcc = np.linalg.norm(ref_mfccs - src_mfccs)
        elif mfcc_distance_metric == 'cosine':
            # Cosine distance: Measures the angle between two vectors, ignoring their
            # magnitude. It's useful for comparing the "shape" of the feature vectors.
            # Cosine SIMILARITY is dot(a,b) / (norm(a)*norm(b)), ranging from -1 to 1.
            # We convert it to a distance metric (ranging from 0 to 2) via `1 - similarity`.
            norm_ref = np.linalg.norm(ref_mfccs)
            norm_src = np.linalg.norm(src_mfccs)
            if norm_ref == 0 or norm_src == 0:
                # If one vector is all zeros, they are maximally dissimilar.
                dist_mfcc = 1.0 
            else:
                cosine_sim = np.dot(ref_mfccs, src_mfccs) / (norm_ref * norm_src)
                dist_mfcc = 1 - cosine_sim # Convert similarity to distance.
        else:
            # This will catch any metric names that are passed but not implemented.
            raise ValueError(f"Unknown MFCC distance metric: {mfcc_distance_metric}")

        # Calculate the total weighted distance
        total_distance = (w_rms * dist_rms) + (w_pitch * dist_pitch) + (w_mfcc * dist_mfcc)

        if use_duration_match:
            dist_duration = abs(ref_duration - src_duration)
            total_distance += (w_duration * dist_duration)

        if total_distance < min_distance:
            min_distance = total_distance
            best_match = source_chunk

    return best_match

def normalize_features(all_chunks):
    """
    Normalizes features across all chunks to a [0, 1] range.
    This is crucial for ensuring that one feature (like MFCC distance)
    doesn't dominate the others in the distance calculation.
    """
    print("Normalizing features...")
    # Extract all values for each feature
    all_rms = [c.features['rms'] for c in all_chunks]
    all_pitches = [c.features['pitch'] for c in all_chunks]
    all_durations = [c.features['duration'] for c in all_chunks]
    
    # Min-max normalization for scalar features
    min_rms, max_rms = min(all_rms), max(all_rms)
    min_pitch, max_pitch = min(all_pitches), max(all_pitches)
    min_duration, max_duration = min(all_durations), max(all_durations)

    # For MFCCs, we normalize each coefficient across all chunks
    all_mfccs = np.array([c.features['mfccs'] for c in all_chunks])
    min_mfccs = np.min(all_mfccs, axis=0)
    max_mfccs = np.max(all_mfccs, axis=0)
    
    for chunk in tqdm(all_chunks, desc="Applying normalization"):
        # Handle potential division by zero if all values are the same
        norm_rms = (chunk.features['rms'] - min_rms) / (max_rms - min_rms) if (max_rms - min_rms) != 0 else 0.5
        norm_pitch = (chunk.features['pitch'] - min_pitch) / (max_pitch - min_pitch) if (max_pitch - min_pitch) != 0 else 0.5
        norm_duration = (chunk.features['duration'] - min_duration) / (max_duration - min_duration) if (max_duration - min_duration) != 0 else 0.5
        # Add a small epsilon to avoid division by zero for MFCCs
        norm_mfccs = (chunk.features['mfccs'] - min_mfccs) / (max_mfccs - min_mfccs + 1e-9)
        
        # CORRECTED: This was assigning an attribute correctly, but the init is now more explicit
        chunk.norm_features = {
            'rms': norm_rms,
            'pitch': norm_pitch,
            'mfccs': norm_mfccs,
            'duration': norm_duration
        }

def concatenate_with_crossfade(chunks, fade_duration_s, sample_rate):
    """Concatenates a list of audio chunks with a linear crossfade."""
    if not chunks:
        return np.array([])
    if len(chunks) == 1:
        return chunks[0].audio

    print("Concatenating chunks with crossfade...")
    fade_samples = int(fade_duration_s * sample_rate)
    
    # Start with the first chunk's audio
    output = chunks[0].audio.copy()
    
    for i in tqdm(range(1, len(chunks)), desc="Crossfading"):
        next_chunk_audio = chunks[i].audio
        
        # Determine overlap size
        overlap_len = min(fade_samples, len(output), len(next_chunk_audio))
        
        if overlap_len == 0:
            output = np.concatenate((output, next_chunk_audio))
            continue
            
        # Create fade ramps
        fade_out = np.linspace(1, 0, overlap_len)
        fade_in = np.linspace(0, 1, overlap_len)
        
        # The crossfaded section
        crossfaded_section = (output[-overlap_len:] * fade_out) + (next_chunk_audio[:overlap_len] * fade_in)
        
        # Concatenate all parts
        output = np.concatenate((output[:-overlap_len], crossfaded_section, next_chunk_audio[overlap_len:]))
        
    return output

# --- Main Execution Block ---
def main():
    parser = argparse.ArgumentParser(description="Reconstructs a reference audio file from source audio files.")
    parser.add_argument('-r', '--reference', type=str, required=True, help="Path to the reference audio file.")
    parser.add_argument('-s', '--sources', nargs='+', required=True, help="Paths to one or more source audio files.")
    parser.add_argument('-o', '--output', type=str, required=True, help="Path for the output audio file.")
    parser.add_argument('--chunk-size-min', type=float, default=0.1, help="Minimum duration of each chunk in seconds. Default: 0.1")
    parser.add_argument('--chunk-size-max', type=float, default=0.4, help="Maximum duration of each chunk in seconds. Default: 0.4")
    parser.add_argument('--no-crossfade', dest='crossfade', action='store_false', help="Disable crossfading between chunks.")
    # HOW TO ADD A NEW METRIC: Add your new metric name to the 'choices' list below.
    parser.add_argument('--mfcc-distance-metric', type=str, choices=['euclidean', 'cosine'], default='euclidean', help="Distance metric for MFCCs. Choices: 'euclidean', 'cosine'. Default: 'euclidean'.")
    parser.add_argument('--weight-rms', type=float, default=1.0, help="Weight for RMS (loudness) matching. Default: 1.0")
    parser.add_argument('--weight-pitch', type=float, default=1.5, help="Weight for pitch matching. Default: 1.5")
    parser.add_argument('--weight-mfcc', type=float, default=1.0, help="Weight for MFCC (timbre) matching. Default: 1.0")
    parser.add_argument('--weight-duration', type=float, default=0.5, help="Weight for duration matching. Default: 0.5")
    parser.add_argument('--crossfade-duration', type=float, default=0.01, help="Duration of the crossfade in seconds. Default: 0.01")
    parser.add_argument('--no-chunk-duration-match', dest='duration_match', action='store_false', help="Disable matching based on chunk duration.")
    parser.add_argument('--adjust-pitch', action='store_true', help="Adjust the pitch of each source chunk to match the reference chunk (autotune effect).")
    parser.add_argument('--sr', type=int, default=22050, help="Sample rate to use for all processing. All files will be resampled to this rate.")
    
    args = parser.parse_args()

    # Validate chunk sizes
    if args.chunk_size_min >= args.chunk_size_max:
        print("Error: --chunk-size-min must be smaller than --chunk-size-max.")
        return
    if args.chunk_size_min <= 0:
        print("Error: --chunk-size-min must be positive.")
        return

    # --- 1. Analysis Phase ---
    # Analyze the reference file
    reference_chunks = analyze_file(args.reference, args.chunk_size_min, args.chunk_size_max, args.sr)
    if not reference_chunks:
        print("Could not process reference file. Exiting.")
        return

    # Analyze all source files and create a single pool of chunks
    source_pool = []
    for source_file in args.sources:
        source_pool.extend(analyze_file(source_file, args.chunk_size_min, args.chunk_size_max, args.sr))
    
    if not source_pool:
        print("Could not process any source files. Exiting.")
        return

    # --- 2. Normalization ---
    # Combine all chunks to normalize features across the entire dataset
    all_chunks_for_norm = reference_chunks + source_pool
    normalize_features(all_chunks_for_norm)

    # --- 3. Matching Phase ---
    print("Finding best matches for each reference chunk...")
    output_chunks = []
    
    # These weights determine the importance of matching each feature.
    # You can experiment with these values to change the output.
    # For example, increasing 'w_pitch' will prioritize matching the melody.
    feature_weights = { # Weights are now configurable via command-line arguments
        'rms': args.weight_rms,
        'pitch': args.weight_pitch,
        'mfcc': args.weight_mfcc,
        'duration': args.weight_duration
    }

    for ref_chunk in tqdm(reference_chunks, desc="Finding best matches"):
        best_source_chunk = find_best_match(ref_chunk, source_pool, feature_weights, args.duration_match, args.mfcc_distance_metric)
        if best_source_chunk:
            chunk_to_add = best_source_chunk

            # --- Pitch Adjustment Logic (Optional) ---
            # If enabled, this acts like an autotuner, shifting the pitch of the
            # source chunk to match the pitch of the reference chunk.
            if args.adjust_pitch:
                # Get the original, non-normalized pitches in Hz
                ref_pitch_hz = ref_chunk.features['pitch']
                src_pitch_hz = best_source_chunk.features['pitch']

                # Only attempt to shift if both pitches were detected and are valid
                if ref_pitch_hz > 0 and src_pitch_hz > 0:
                    # Calculate the pitch difference in semitones
                    n_semitones = 12 * np.log2(ref_pitch_hz / src_pitch_hz)
                    
                    # Create a deep copy to avoid modifying the original chunk in the source pool
                    adjusted_chunk = copy.deepcopy(best_source_chunk)
                    
                    # Apply pitch shifting to the audio data of the copied chunk
                    adjusted_chunk.audio = librosa.effects.pitch_shift(
                        y=adjusted_chunk.audio, sr=adjusted_chunk.sr, n_steps=n_semitones
                    )
                    chunk_to_add = adjusted_chunk
            
            output_chunks.append(chunk_to_add)

    # --- 4. Synthesis Phase ---
    if args.crossfade:
        final_audio = concatenate_with_crossfade(output_chunks, args.crossfade_duration, args.sr)
    else:
        print("Synthesizing output file (no crossfade)...")
        # Concatenate the audio data from the chosen chunks
        final_audio = np.concatenate([chunk.audio for chunk in output_chunks])
    
    # Write the final audio to a file
    try:
        sf.write(args.output, final_audio, args.sr)
        print(f"\nSuccess! Output saved to: {args.output}")
    except Exception as e:
        print(f"Error writing output file: {e}")

if __name__ == '__main__':
    main()
