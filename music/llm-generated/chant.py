import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
import random

class SyntheticChantGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
        # Formant frequencies for "Chant" vowels (darker, more open)
        # We emphasize O, U, A, and minimize bright I/E sounds
        self.vowels = {
            'a': [700, 1200], # Open 'Ah'
            'o': [500, 900],  # Deep 'Oh'
            'u': [300, 800],  # Deep 'Oo'
            'ae': [600, 1600] # Neutral 'Eh'
        }
        
        # Musical Scale (frequencies relative to a root note)
        # Using a Minor Pentatonic scale for that "solemn" feel
        # Intervals: Root, min3, 4, 5, min7
        #self.scale_intervals = [1.0, 1.2, 1.33, 1.5, 1.78]
        self.scale_intervals = [1.0, 1.31, 0.34, 1.57, 2.12, 2.03, 0.85, 1.02, 0.93] # self.scale_intervals = [1.0, 1.21, 1.34, 1.57, 1.98]

    def generate_harmonic_source(self, duration, f0):
        """
        Generates a rich, resonant source wave.
        Combines a sawtooth (buzz) with a sine (fundamental) for depth.
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        
        # Main oscillating tone
        audio = 0.6 * signal.sawtooth(2 * np.pi * f0 * t, width=0.5)
        audio += 0.4 * np.sin(2 * np.pi * f0 * t) # Add body
        
        # Low pass filter to remove harsh digital sizzle
        b, a = signal.butter(2, 2500 / (self.sample_rate / 2), btype='low')
        audio = signal.lfilter(b, a, audio)
        
        return audio

    def generate_soft_consonant(self, duration):
        """
        Generates soft breathy noises (h, sh, m) rather than harsh clicks.
        """
        samples = int(self.sample_rate * duration)
        noise = np.random.normal(0, 1, samples)
        
        # Bandpass filter to make it sound like "wind" or breath
        #b, a = signal.butter(2, [500/(self.sample_rate/2), 2000/(self.sample_rate/2)], btype='band')
        b, a = signal.butter(2, [500/(self.sample_rate/2), 700/(self.sample_rate/2)], btype='band')
        filtered_noise = signal.lfilter(b, a, noise)
        
        return filtered_noise * 0.3

    def apply_vocal_tract(self, audio, formants):
        """
        Filters the source to sound like a human vowel.
        """
        output = np.zeros_like(audio)
        for f in formants:
            # Fixed bandwidth for resonance
            bw = 80  
            Q = f / bw
            b, a = signal.iirpeak(f, Q, fs=self.sample_rate)
            output += signal.lfilter(b, a, audio)
        return output

    def apply_envelope(self, audio, attack_sec=0.2, release_sec=0.3):
        """
        Slow attack and release for legato (smooth) singing.
        """
        samples = len(audio)
        attack_samples = int(attack_sec * self.sample_rate)
        release_samples = int(release_sec * self.sample_rate)
        
        # Safety check for very short clips
        if samples < (attack_samples + release_samples):
            return audio * signal.windows.hann(samples)
            
        env = np.ones(samples)
        env[:attack_samples] = np.linspace(0, 1, attack_samples)
        env[-release_samples:] = np.linspace(1, 0, release_samples)
        return audio * env

    def add_cathedral_reverb(self, audio, delay_sec=0.4, decay=0.6):
        """
        Simple feedback delay line to simulate a large stone room.
        """
        delay_samples = int(delay_sec * self.sample_rate)
        output = np.zeros(len(audio) + delay_samples * 4)
        output[:len(audio)] = audio
        
        # 3 iterations of echo
        for i in range(1, 4):
            start = i * delay_samples
            end = start + len(audio)
            # Add delayed copy with volume reduction
            output[start:end] += audio * (decay ** i)
            
        # Normalize
        return output / np.max(np.abs(output))

    def generate(self, duration_sec, output_file="synthetic_chant.wav"):
        print(f"Generating {duration_sec}s chant...")
        
        # Pick a random Root Note for this session (Low male range: G2 to C3)
        root_freq = random.uniform(98, 130) 
        
        full_audio = []
        current_time = 0
        
        # State machine for singing
        last_pitch = root_freq
        
        while current_time < duration_sec:
            # 1. Pick duration (Long, drawn out notes)
            note_dur = random.uniform(1.5, 3.5)
            
            # 2. Pick Pitch (Move stepwise up or down scale, rarely jump)
            scale_multiplier = random.choice(self.scale_intervals)
            current_pitch = root_freq * scale_multiplier
            
            # 3. Generate Tone
            raw_source = self.generate_harmonic_source(note_dur, current_pitch)
            
            # 4. Pick Vowel (randomly change vowel or keep same)
            vowel_key = random.choice(list(self.vowels.keys()))
            formants = self.vowels[vowel_key]
            
            # 5. Filter
            sung_note = self.apply_vocal_tract(raw_source, formants)
            sung_note = self.apply_envelope(sung_note, attack_sec=0.3, release_sec=0.3)
            
            # 6. Occasionally add a "consonant" transition (soft 'm' or 'h')
            if random.random() < 0.3:#and 0 > 1: # just to comment this
                breath_dur = 0.2
                breath = self.generate_soft_consonant(breath_dur)
                breath = self.apply_envelope(breath, 0.05, 0.05)
                full_audio.append(breath)
                current_time += breath_dur

            full_audio.append(sung_note)
            current_time += note_dur

        # Concatenate
        dry_signal = np.concatenate(full_audio)
        
        # Trim main clip (allow tail for reverb later)
        target_samples = int(duration_sec * self.sample_rate)
        if len(dry_signal) > target_samples:
            dry_signal = dry_signal[:target_samples]
            
        # Apply Reverb
        wet_signal = self.add_cathedral_reverb(dry_signal)
        
        # Final Normalize and Save
        wet_signal = wet_signal / np.max(np.abs(wet_signal))
        wet_signal = (wet_signal * 32767).astype(np.int16)
        
        wavfile.write(output_file, self.sample_rate, wet_signal)
        print(f"Chant saved to {output_file}")

if __name__ == "__main__":
    # Input Parameter: Duration
    DURATION = 90.0
    
    chanter = SyntheticChantGenerator()
    chanter.generate(DURATION)
