import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
import random

class SyntheticSpeechGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
        # Formant frequencies for vowels (F1, F2) in Hz
        # We simulate generic vowel sounds: a, e, i, o, u
        self.vowels = {
            'a': [730, 1090],
            'e': [530, 1840],
            'i': [270, 2290],
            'o': [570, 840],
            'u': [300, 870]
        }

    def generate_glottal_source(self, duration, f0):
        """
        Generates a buzzy 'voiced' source (like vocal cords vibrating).
        Uses a sawtooth wave with slight frequency jitter for naturalness.
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        
        # Add slight jitter to frequency to simulate natural voice imperfection
        jitter = np.random.uniform(-0.5, 0.5, size=t.shape)
        
        # Generate Sawtooth wave (rich in harmonics)
        # We modulate the phase slightly to prevent it sounding like an NES game
        audio = signal.sawtooth(2 * np.pi * (f0 + jitter) * t, width=0.5)
        
        # Soften the buzz slightly
        b, a = signal.butter(2, 3000 / (self.sample_rate / 2), btype='low')
        audio = signal.lfilter(b, a, audio)
        
        return audio

    def generate_noise_source(self, duration):
        """
        Generates an 'unvoiced' source (like hissing/air) for consonants.
        """
        samples = int(self.sample_rate * duration)
        # White noise
        noise = np.random.normal(0, 1, samples)
        
        # High pass filter to simulate sibilance (s, t, sh sounds)
        b, a = signal.butter(2, 2000 / (self.sample_rate / 2), btype='high')
        filtered_noise = signal.lfilter(b, a, noise)
        
        return filtered_noise

    def apply_formants(self, audio, formants, gender_shift):
        """
        Applies bandpass filters to simulate the shape of the mouth/throat.
        gender_shift: shifts formants higher for female voices.
        """
        output = np.zeros_like(audio)
        
        # Shift formants based on gender (smaller vocal tracts = higher formants)
        # Shift factor: 1.0 (Male) to ~1.2 (Female)
        shift_factor = 1.0 + (gender_shift * 0.2)
        
        for f in formants:
            # Calculate target frequency
            center_freq = f * shift_factor
            
            # Ensure we don't exceed Nyquist frequency
            if center_freq >= self.sample_rate / 2:
                center_freq = (self.sample_rate / 2) - 100
            
            # Bandwidth of the formant filter
            bw = 100  
            Q = center_freq / bw
            
            # Apply Peak/Bandpass filter
            b, a = signal.iirpeak(center_freq, Q, fs=self.sample_rate)
            filtered_band = signal.lfilter(b, a, audio)
            output += filtered_band
            
        return output

    def apply_envelope(self, audio, attack=0.01, release=0.01):
        """
        Applies an ADSR-like amplitude envelope to prevent clicking at edges.
        """
        samples = len(audio)
        attack_samples = int(attack * self.sample_rate)
        release_samples = int(release * self.sample_rate)
        
        if samples < (attack_samples + release_samples):
            # If segment is too short, just window the whole thing
            return audio * signal.windows.hann(samples)
            
        env = np.ones(samples)
        # Fade in
        env[:attack_samples] = np.linspace(0, 1, attack_samples)
        # Fade out
        env[-release_samples:] = np.linspace(1, 0, release_samples)
        
        return audio * env

    def generate_speech(self, duration_sec, gender, consonant_pct, output_file="synthetic_speech.wav"):
        """
        Main generation loop.
        gender: 0.0 (Male) -> 1.0 (Female)
        consonant_pct: 0.0 -> 1.0
        """
        print(f"Generating {duration_sec}s | Gender: {gender} | Consonants: {consonant_pct*100}%")
        
        # Pitch Logic
        # Male base ~100Hz, Female base ~220Hz
        base_pitch = 100 + (gender * 120)
        
        full_audio = []
        current_time = 0
        
        while current_time < duration_sec:
            # Decide if Consonant or Vowel
            is_consonant = random.random() < consonant_pct
            
            # Duration of this specific phoneme (randomized)
            # Consonants are usually shorter/snappier
            if is_consonant:
                phoneme_dur = random.uniform(0.05, 0.15)
                # Generate Noise
                chunk = self.generate_noise_source(phoneme_dur)
                # Amplitude check (consonants are often quieter)
                chunk = chunk * 0.5
            else:
                phoneme_dur = random.uniform(0.1, 0.3)
                # Add intonation (pitch wandering)
                pitch_drift = random.uniform(-10, 10)
                current_pitch = base_pitch + pitch_drift
                
                # Generate Source
                raw_source = self.generate_glottal_source(phoneme_dur, current_pitch)
                
                # Pick a random vowel shape
                vowel_key = random.choice(list(self.vowels.keys()))
                formants = self.vowels[vowel_key]
                
                # Apply Filters
                chunk = self.apply_formants(raw_source, formants, gender)
            
            # Apply envelope to phoneme
            chunk = self.apply_envelope(chunk)
            
            # Append to buffer
            full_audio.append(chunk)
            current_time += phoneme_dur
            
            # Occasionally insert a "breath" or word pause (silence)
            if random.random() < 0.15:
                pause_dur = random.uniform(0.05, 0.2)
                pause_samples = int(pause_dur * self.sample_rate)
                full_audio.append(np.zeros(pause_samples))
                current_time += pause_dur

        # Concatenate all chunks
        final_signal = np.concatenate(full_audio)
        
        # Trim or Pad to exact requested duration
        target_samples = int(duration_sec * self.sample_rate)
        if len(final_signal) > target_samples:
            final_signal = final_signal[:target_samples]
        else:
            final_signal = np.pad(final_signal, (0, target_samples - len(final_signal)))

        # Normalize Volume
        max_val = np.max(np.abs(final_signal))
        if max_val > 0:
            final_signal = final_signal / max_val
            
        # Convert to 16-bit PCM for WAV
        final_signal = (final_signal * 32767).astype(np.int16)
        
        wavfile.write(output_file, self.sample_rate, final_signal)
        print(f"Saved to {output_file}")

# --- Configuration Area ---
if __name__ == "__main__":
    
    # 1. Output Length (seconds)
    LENGTH = 10.0 
    
    # 2. Voice Gender (0.0 = Deep Male, 1.0 = High Female)
    GENDER = 0.0
    
    # 3. Consonant Percentage (0.0 = All vowels/chanting, 1.0 = All noise/whispering)
    CONSONANT_PCT = 0.0
    
    generator = SyntheticSpeechGenerator()
    generator.generate_speech(LENGTH, GENDER, CONSONANT_PCT)
