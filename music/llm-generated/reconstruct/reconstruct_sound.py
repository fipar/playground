#!/usr/bin/env python3
"""
Audio Reconstruction Tool

Reconstructs a reference audio file using timbral material from source files
while preserving the original pitch and tempo structure.
"""

import argparse
import sys
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import numpy as np
import librosa
import soundfile as sf
from scipy.spatial.distance import cosine, cdist


class AudioAnalyzer:
    """Handles audio analysis including pitch, tempo, and timbre extraction."""
    
    def __init__(self, sr: int = 22050):
        self.sr = sr
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return audio data and sample rate."""
        try:
            audio, sr = librosa.load(file_path, sr=self.sr)
            return audio, sr
        except Exception as e:
            raise ValueError(f"Could not load audio file '{file_path}': {e}")
    
    def extract_pitch(self, audio: np.ndarray) -> float:
        """Extract median fundamental frequency (pitch) from audio - faster single value."""
        if len(audio) < self.sr * 0.1:  # Skip very short chunks
            return 0.0
            
        # Use yin for faster, more accurate pitch detection (skip samplerate dependency)
        try:
            f0 = librosa.yin(audio, fmin=50, fmax=2000, sr=self.sr)
        except:
            # Fallback to simpler pitch detection if yin fails
            stft = librosa.stft(audio)
            freqs = librosa.fft_frequencies(sr=self.sr)
            magnitude = np.abs(stft)
            f0 = freqs[np.argmax(magnitude, axis=0)]
        # Return median pitch, filtering out zeros
        valid_pitches = f0[f0 > 0]
        return np.median(valid_pitches) if len(valid_pitches) > 0 else 0.0
    
    def extract_tempo_beats(self, audio: np.ndarray) -> Tuple[float, np.ndarray]:
        """Extract tempo and beat positions from audio."""
        tempo, beats = librosa.beat.beat_track(y=audio, sr=self.sr)
        return tempo, beats
    
    def extract_mfcc(self, audio: np.ndarray, n_mfcc: int = 13) -> np.ndarray:
        """Extract MFCC features for timbral analysis."""
        if len(audio) < 512:  # Too short for meaningful MFCC
            return np.zeros(n_mfcc)
        
        # Use smaller hop length for faster processing
        mfccs = librosa.feature.mfcc(
            y=audio, sr=self.sr, n_mfcc=n_mfcc, 
            hop_length=512, n_fft=1024
        )
        return np.mean(mfccs, axis=1)  # Average across time


class AudioChunker:
    """Handles audio segmentation into chunks."""
    
    def __init__(self, sr: int = 22050):
        self.sr = sr
    
    def chunk_audio(self, audio: np.ndarray, min_chunk_ms: int, max_chunk_ms: int) -> List[Tuple[int, int, np.ndarray]]:
        """
        Segment audio into fixed-size chunks for faster processing.
        Returns list of (start_idx, end_idx, chunk_audio) tuples.
        """
        min_samples = int(min_chunk_ms * self.sr / 1000)
        max_samples = int(max_chunk_ms * self.sr / 1000)
        
        # Use fixed-size chunking for speed instead of onset detection
        chunk_size = max_samples
        chunks = []
        
        for start_idx in range(0, len(audio), chunk_size):
            end_idx = min(start_idx + chunk_size, len(audio))
            
            # Skip chunks that are too small
            if end_idx - start_idx < min_samples:
                break
                
            chunk_audio = audio[start_idx:end_idx]
            chunks.append((start_idx, end_idx, chunk_audio))
        
        return chunks


class TimbralMatcher:
    """Handles timbral matching between reference and source chunks."""
    
    def __init__(self):
        self.analyzer = AudioAnalyzer()
        self.source_mfccs = None
        self.source_chunks = None
    
    def precompute_source_features(self, source_chunks: List[Tuple[int, int, np.ndarray]]):
        """Pre-compute MFCC features for all source chunks for faster matching."""
        print("Pre-computing MFCC features for source chunks...")
        self.source_chunks = source_chunks
        self.source_mfccs = np.array([
            self.analyzer.extract_mfcc(chunk_audio) 
            for _, _, chunk_audio in source_chunks
        ])
    
    def find_best_match(self, ref_chunk: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        Find the source chunk with the most similar timbre to the reference chunk.
        Returns (best_match_index, best_match_audio).
        """
        if self.source_mfccs is None or self.source_chunks is None:
            raise ValueError("Must call precompute_source_features first")
            
        ref_mfcc = self.analyzer.extract_mfcc(ref_chunk)
        
        # Vectorized distance computation for all source chunks at once
        distances = cdist([ref_mfcc], self.source_mfccs, metric='cosine')[0]
        best_match_idx = np.argmin(distances)
        
        return best_match_idx, self.source_chunks[best_match_idx][2]


class AudioProcessor:
    """Handles pitch shifting and time stretching operations."""
    
    def __init__(self, sr: int = 22050):
        self.sr = sr
        self.analyzer = AudioAnalyzer(sr)
    
    def pitch_shift(self, audio: np.ndarray, target_pitch: float, source_pitch: float) -> np.ndarray:
        """Shift pitch of audio to match target pitch."""
        if source_pitch <= 0 or target_pitch <= 0:
            return audio  # Cannot shift if pitch is not detected
        
        # Skip pitch shifting if difference is small (< 5%)
        pitch_ratio = target_pitch / source_pitch
        if 0.95 < pitch_ratio < 1.05:
            return audio
        
        # Calculate semitone shift needed
        semitone_shift = 12 * np.log2(pitch_ratio)
        
        # Apply pitch shift with faster parameters (avoid samplerate dependency)
        try:
            shifted_audio = librosa.effects.pitch_shift(
                audio, sr=self.sr, n_steps=semitone_shift, res_type='linear'
            )
        except:
            # Fallback: simple frequency domain pitch shifting
            shifted_audio = librosa.effects.pitch_shift(
                audio, sr=self.sr, n_steps=semitone_shift
            )
        return shifted_audio
    
    def time_stretch(self, audio: np.ndarray, target_duration: float) -> np.ndarray:
        """Time-stretch audio to match target duration."""
        current_duration = len(audio) / self.sr
        stretch_ratio = current_duration / target_duration
        
        if abs(stretch_ratio - 1.0) < 0.05:  # No significant change needed (relaxed threshold)
            return audio
        
        # Use faster time stretching
        stretched_audio = librosa.effects.time_stretch(audio, rate=stretch_ratio)
        return stretched_audio
    
    def apply_attack_envelope(self, audio: np.ndarray, attack_ms: float) -> np.ndarray:
        """Apply attack envelope (fade-in) to audio chunk."""
        if attack_ms <= 0:
            return audio  # No envelope if attack time is 0
        
        attack_samples = int(attack_ms * self.sr / 1000)
        
        # Don't apply envelope if attack time is longer than the audio
        if attack_samples >= len(audio):
            return audio
        
        # Create fade-in envelope
        envelope = np.ones_like(audio)
        fade_in = np.linspace(0, 1, attack_samples)
        envelope[:attack_samples] = fade_in
        
        return audio * envelope


class AudioReconstructor:
    """Main class that orchestrates the audio reconstruction process."""
    
    def __init__(self, sr: int = 22050):
        self.sr = sr
        self.analyzer = AudioAnalyzer(sr)
        self.chunker = AudioChunker(sr)
        self.matcher = TimbralMatcher()
        self.processor = AudioProcessor(sr)
    
    def reconstruct(self, reference_path: str, source_paths: List[str], 
                   min_chunk_ms: int, max_chunk_ms: int, output_path: str, attack_ms: float = 0.0):
        """Main reconstruction method."""
        print("Loading reference audio...")
        ref_audio, _ = self.analyzer.load_audio(reference_path)
        
        print("Loading source audio files...")
        source_audios = []
        for source_path in source_paths:
            source_audio, _ = self.analyzer.load_audio(source_path)
            source_audios.append(source_audio)
        
        print("Chunking reference audio...")
        ref_chunks = self.chunker.chunk_audio(ref_audio, min_chunk_ms, max_chunk_ms)
        
        print("Chunking source audio files...")
        all_source_chunks = []
        for source_audio in source_audios:
            source_chunks = self.chunker.chunk_audio(source_audio, min_chunk_ms, max_chunk_ms)
            all_source_chunks.extend(source_chunks)
        
        if not all_source_chunks:
            raise ValueError("No source chunks found. Check audio files and chunk size parameters.")
        
        # Pre-compute source chunk features for faster matching
        self.matcher.precompute_source_features(all_source_chunks)
        
        # Pre-compute reference chunk pitches
        print("Pre-computing reference chunk features...")
        ref_pitches = []
        for _, _, ref_chunk_audio in ref_chunks:
            ref_pitch = self.analyzer.extract_pitch(ref_chunk_audio)
            ref_pitches.append(ref_pitch)
        
        # Pre-compute source chunk pitches
        print("Pre-computing source chunk pitches...")
        source_pitches = []
        for _, _, source_chunk_audio in all_source_chunks:
            source_pitch = self.analyzer.extract_pitch(source_chunk_audio)
            source_pitches.append(source_pitch)
        
        print(f"Processing {len(ref_chunks)} reference chunks...")
        reconstructed_audio = []
        
        for i, (start_idx, end_idx, ref_chunk_audio) in enumerate(ref_chunks):
            if i % 10 == 0:
                print(f"Processing chunk {i+1}/{len(ref_chunks)}...")
            
            # Find best matching source chunk (now much faster)
            best_match_idx, matched_audio = self.matcher.find_best_match(ref_chunk_audio)
            
            # Use pre-computed pitches
            ref_pitch = ref_pitches[i]
            source_pitch = source_pitches[best_match_idx]
            
            # Apply pitch shifting
            if ref_pitch > 0 and source_pitch > 0:
                matched_audio = self.processor.pitch_shift(matched_audio, ref_pitch, source_pitch)
            
            # Apply time stretching to match reference chunk duration
            ref_duration = len(ref_chunk_audio) / self.sr
            matched_audio = self.processor.time_stretch(matched_audio, ref_duration)
            
            # Apply attack envelope if specified
            if attack_ms > 0:
                matched_audio = self.processor.apply_attack_envelope(matched_audio, attack_ms)
            
            # Ensure exact length match by padding or trimming
            target_length = len(ref_chunk_audio)
            if len(matched_audio) > target_length:
                matched_audio = matched_audio[:target_length]
            elif len(matched_audio) < target_length:
                padding = np.zeros(target_length - len(matched_audio))
                matched_audio = np.concatenate([matched_audio, padding])
            
            reconstructed_audio.append(matched_audio)
        
        # Concatenate all processed chunks
        final_audio = np.concatenate(reconstructed_audio)
        
        print(f"Saving reconstructed audio to {output_path}...")
        sf.write(output_path, final_audio, self.sr)
        print("Reconstruction complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Reconstruct audio using timbral material from source files"
    )
    
    parser.add_argument(
        "-source", required=True,
        help="Comma-separated list of source audio file paths"
    )
    parser.add_argument(
        "-reference", required=True,
        help="Path to reference audio file"
    )
    parser.add_argument(
        "-min-chunk", type=int, required=True,
        help="Minimum chunk size in milliseconds"
    )
    parser.add_argument(
        "-max-chunk", type=int, required=True,
        help="Maximum chunk size in milliseconds"
    )
    parser.add_argument(
        "-output", 
        help="Output file path (default: reconstruction_YYYY-MM-DD_HHMMSS.wav)"
    )
    parser.add_argument(
        "-attack", type=float, default=0.0,
        help="Attack time in milliseconds for amplitude envelope of each chunk (default: 0)"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.reference):
        print(f"Error: Reference file '{args.reference}' not found.", file=sys.stderr)
        sys.exit(1)
    
    source_paths = [path.strip() for path in args.source.split(',')]
    for source_path in source_paths:
        if not os.path.exists(source_path):
            print(f"Error: Source file '{source_path}' not found.", file=sys.stderr)
            sys.exit(1)
    
    if args.min_chunk <= 0 or args.max_chunk <= 0:
        print("Error: Chunk sizes must be positive integers.", file=sys.stderr)
        sys.exit(1)
    
    if args.min_chunk > args.max_chunk:
        print("Error: Minimum chunk size cannot be larger than maximum chunk size.", file=sys.stderr)
        sys.exit(1)
    
    if args.attack < 0:
        print("Error: Attack time must be non-negative.", file=sys.stderr)
        sys.exit(1)
    
    # Generate default output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        args.output = f"reconstruction_{timestamp}.wav"
    
    try:
        reconstructor = AudioReconstructor()
        reconstructor.reconstruct(
            args.reference, source_paths, 
            args.min_chunk, args.max_chunk, 
            args.output, args.attack
        )
    except Exception as e:
        print(f"Error during reconstruction: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()