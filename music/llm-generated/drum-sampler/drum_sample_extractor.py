#!/usr/bin/env python3

import numpy as np
import librosa
import soundfile as sf
import os
import argparse
from scipy import signal
from scipy.spatial.distance import euclidean
import matplotlib.pyplot as plt

class DrumSampleExtractor:
    def __init__(self, input_file, output_dir, sample_duration=0.5):
        self.input_file = input_file
        self.output_dir = output_dir
        self.sample_duration = sample_duration
        
        # Load audio
        self.audio, self.sr = librosa.load(input_file, sr=None)
        
        # Drum sound characteristics (frequency ranges in Hz and envelope shapes)
        self.drum_characteristics = {
            'kick': {
                'freq_range': (20, 120),
                'freq_peak': 60,
                'envelope_shape': 'exponential_decay',
                'min_duration': 0.1,
                'max_duration': 0.8
            },
            'snare': {
                'freq_range': (150, 6000),
                'freq_peak': 200,
                'envelope_shape': 'sharp_attack',
                'min_duration': 0.05,
                'max_duration': 0.3
            },
            'hihat_closed': {
                'freq_range': (8000, 20000),
                'freq_peak': 10000,
                'envelope_shape': 'quick_decay',
                'min_duration': 0.02,
                'max_duration': 0.15
            },
            'hihat_open': {
                'freq_range': (8000, 20000),
                'freq_peak': 12000,
                'envelope_shape': 'sustained_decay',
                'min_duration': 0.1,
                'max_duration': 0.6
            },
            'tom': {
                'freq_range': (80, 400),
                'freq_peak': 120,
                'envelope_shape': 'exponential_decay',
                'min_duration': 0.08,
                'max_duration': 0.5
            },
            'crash': {
                'freq_range': (3000, 20000),
                'freq_peak': 8000,
                'envelope_shape': 'long_decay',
                'min_duration': 0.5,
                'max_duration': 3.0
            }
        }
        
        os.makedirs(output_dir, exist_ok=True)
    
    def detect_onsets(self, hop_length=512):
        """Detect onset times in the audio"""
        onset_frames = librosa.onset.onset_detect(
            y=self.audio,
            sr=self.sr,
            hop_length=hop_length,
            backtrack=True,
            units='frames'
        )
        onset_times = librosa.frames_to_time(onset_frames, sr=self.sr, hop_length=hop_length)
        return onset_times
    
    def extract_segments(self, onset_times, min_gap=0.05):
        """Extract audio segments around onset times"""
        segments = []
        
        for i, onset in enumerate(onset_times):
            start_time = max(0, onset - 0.01)  # Small pre-attack
            
            # Determine end time based on next onset or maximum duration
            if i + 1 < len(onset_times):
                next_onset = onset_times[i + 1]
                end_time = min(onset + self.sample_duration, next_onset - min_gap)
            else:
                end_time = min(onset + self.sample_duration, len(self.audio) / self.sr)
            
            if end_time - start_time > 0.02:  # Minimum segment length
                start_sample = int(start_time * self.sr)
                end_sample = int(end_time * self.sr)
                segment = self.audio[start_sample:end_sample]
                
                segments.append({
                    'audio': segment,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time
                })
        
        return segments
    
    def analyze_frequency_content(self, segment_audio):
        """Analyze the frequency content of a segment"""
        # Compute FFT
        fft = np.fft.rfft(segment_audio)
        freqs = np.fft.rfftfreq(len(segment_audio), 1/self.sr)
        magnitude = np.abs(fft)
        
        # Find dominant frequencies
        peak_idx = np.argmax(magnitude)
        dominant_freq = freqs[peak_idx]
        
        # Compute spectral centroid
        spectral_centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
        
        # Compute energy in different frequency bands
        low_energy = np.sum(magnitude[(freqs >= 20) & (freqs <= 200)])
        mid_energy = np.sum(magnitude[(freqs >= 200) & (freqs <= 2000)])
        high_energy = np.sum(magnitude[(freqs >= 2000) & (freqs <= 20000)])
        
        return {
            'dominant_freq': dominant_freq,
            'spectral_centroid': spectral_centroid,
            'low_energy': low_energy,
            'mid_energy': mid_energy,
            'high_energy': high_energy,
            'total_energy': np.sum(magnitude)
        }
    
    def analyze_envelope(self, segment_audio):
        """Analyze the amplitude envelope of a segment"""
        # Compute envelope using Hilbert transform
        analytic_signal = signal.hilbert(segment_audio)
        envelope = np.abs(analytic_signal)
        
        # Smooth envelope
        window_size = max(1, len(envelope) // 50)
        envelope = np.convolve(envelope, np.ones(window_size)/window_size, mode='same')
        
        # Normalize envelope
        if np.max(envelope) > 0:
            envelope = envelope / np.max(envelope)
        
        # Envelope characteristics
        peak_idx = np.argmax(envelope)
        peak_position = peak_idx / len(envelope)
        
        # Attack time (time to reach 90% of peak)
        peak_val = envelope[peak_idx]
        attack_threshold = 0.9 * peak_val
        attack_idx = np.where(envelope >= attack_threshold)[0]
        attack_time = attack_idx[0] / len(envelope) if len(attack_idx) > 0 else 0
        
        # Decay characteristics
        if peak_idx < len(envelope) - 1:
            decay_portion = envelope[peak_idx:]
            decay_rate = np.mean(np.diff(decay_portion)) if len(decay_portion) > 1 else 0
        else:
            decay_rate = 0
        
        return {
            'envelope': envelope,
            'peak_position': peak_position,
            'attack_time': attack_time,
            'decay_rate': decay_rate,
            'sustain_level': np.mean(envelope[len(envelope)//2:]) if len(envelope) > 2 else 0
        }
    
    def classify_drum_sound(self, segment, freq_analysis, envelope_analysis):
        """Classify a segment as a specific drum sound type"""
        scores = {}
        
        for drum_type, characteristics in self.drum_characteristics.items():
            score = 0
            
            # Duration check
            duration = segment['duration']
            if characteristics['min_duration'] <= duration <= characteristics['max_duration']:
                score += 20
            
            # Frequency matching
            freq_min, freq_max = characteristics['freq_range']
            dominant_freq = freq_analysis['dominant_freq']
            
            if freq_min <= dominant_freq <= freq_max:
                score += 30
                
                # Bonus for being near peak frequency
                freq_distance = abs(dominant_freq - characteristics['freq_peak'])
                freq_bonus = max(0, 20 - freq_distance / characteristics['freq_peak'] * 20)
                score += freq_bonus
            
            # Energy distribution matching
            total_energy = freq_analysis['total_energy']
            if total_energy > 0:
                low_ratio = freq_analysis['low_energy'] / total_energy
                high_ratio = freq_analysis['high_energy'] / total_energy
                
                if drum_type == 'kick':
                    score += low_ratio * 20
                elif drum_type in ['hihat_closed', 'hihat_open', 'crash']:
                    score += high_ratio * 20
                elif drum_type == 'snare':
                    mid_ratio = freq_analysis['mid_energy'] / total_energy
                    score += mid_ratio * 15 + high_ratio * 10
            
            # Envelope matching
            envelope_shape = characteristics['envelope_shape']
            if envelope_shape == 'exponential_decay' and envelope_analysis['decay_rate'] < -0.01:
                score += 15
            elif envelope_shape == 'sharp_attack' and envelope_analysis['attack_time'] < 0.1:
                score += 15
            elif envelope_shape == 'quick_decay' and envelope_analysis['decay_rate'] < -0.02:
                score += 15
            elif envelope_shape == 'sustained_decay' and envelope_analysis['sustain_level'] > 0.1:
                score += 15
            elif envelope_shape == 'long_decay' and envelope_analysis['sustain_level'] > 0.2:
                score += 15
            
            scores[drum_type] = score
        
        return scores
    
    def extract_best_samples(self, segments, num_samples_per_type=3):
        """Extract the best samples for each drum type"""
        drum_samples = {drum_type: [] for drum_type in self.drum_characteristics.keys()}
        
        # Analyze each segment
        for segment in segments:
            freq_analysis = self.analyze_frequency_content(segment['audio'])
            envelope_analysis = self.analyze_envelope(segment['audio'])
            
            # Classify the segment
            scores = self.classify_drum_sound(segment, freq_analysis, envelope_analysis)
            
            # Find best match
            best_drum_type = max(scores, key=scores.get)
            best_score = scores[best_drum_type]
            
            # Only consider segments with reasonable scores
            if best_score > 30:
                segment_data = {
                    'segment': segment,
                    'score': best_score,
                    'freq_analysis': freq_analysis,
                    'envelope_analysis': envelope_analysis
                }
                drum_samples[best_drum_type].append(segment_data)
        
        # Keep only the best samples for each drum type
        for drum_type in drum_samples:
            drum_samples[drum_type].sort(key=lambda x: x['score'], reverse=True)
            drum_samples[drum_type] = drum_samples[drum_type][:num_samples_per_type]
        
        return drum_samples
    
    def save_samples(self, drum_samples):
        """Save the extracted samples to files"""
        saved_files = []
        
        for drum_type, samples in drum_samples.items():
            if not samples:
                print(f"No samples found for {drum_type}")
                continue
            
            for i, sample_data in enumerate(samples):
                filename = f"{drum_type}_{i+1:02d}.wav"
                filepath = os.path.join(self.output_dir, filename)
                
                # Save the audio
                sf.write(filepath, sample_data['segment']['audio'], self.sr)
                saved_files.append(filepath)
                
                print(f"Saved {filename} (score: {sample_data['score']:.1f})")
        
        return saved_files
    
    def process(self):
        """Main processing function"""
        print(f"Processing audio file: {self.input_file}")
        print(f"Audio duration: {len(self.audio) / self.sr:.2f}s")
        print(f"Sample rate: {self.sr}Hz")
        
        # Detect onsets
        print("\nDetecting onsets...")
        onset_times = self.detect_onsets()
        print(f"Found {len(onset_times)} onsets")
        
        # Extract segments
        print("\nExtracting segments...")
        segments = self.extract_segments(onset_times)
        print(f"Extracted {len(segments)} segments")
        
        # Extract and classify samples
        print("\nAnalyzing and classifying segments...")
        drum_samples = self.extract_best_samples(segments)
        
        # Save samples
        print(f"\nSaving samples to {self.output_dir}...")
        saved_files = self.save_samples(drum_samples)
        
        print(f"\nExtraction complete! Saved {len(saved_files)} samples.")
        return saved_files

def main():
    parser = argparse.ArgumentParser(description='Extract drum samples from audio file')
    parser.add_argument('input_file', help='Input audio file path')
    parser.add_argument('output_dir', help='Output directory for samples')
    parser.add_argument('--duration', type=float, default=0.5, 
                       help='Maximum sample duration in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        return
    
    extractor = DrumSampleExtractor(args.input_file, args.output_dir, args.duration)
    extractor.process()

if __name__ == "__main__":
    main()