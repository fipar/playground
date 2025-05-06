#!/usr/bin/env python3
"""
DrumSynth - A command-line drum synthesizer for creating unique drum samples
"""

import os
import sys
import argparse
import random
import time
import numpy as np
from scipy.io import wavfile
import math

# Global parameters
SAMPLE_RATE = 44100  # Sample rate in Hz

class Envelope:
    """ADSR envelope generator for controlling amplitude over time"""
    
    def __init__(self, attack=0.01, decay=0.1, sustain=0.7, release=0.3, amplitude=1.0):
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
        self.amplitude = amplitude
    
    def randomize(self, attack_var=0.1, decay_var=0.1, sustain_var=0.1, release_var=0.1, amp_var=0.1):
        """Create a randomized copy of this envelope"""
        return Envelope(
            attack=max(0.001, self.attack * random.uniform(1.0 - attack_var, 1.0 + attack_var)),
            decay=max(0.001, self.decay * random.uniform(1.0 - decay_var, 1.0 + decay_var)),
            sustain=max(0.0, min(1.0, self.sustain * random.uniform(1.0 - sustain_var, 1.0 + sustain_var))),
            release=max(0.001, self.release * random.uniform(1.0 - release_var, 1.0 + release_var)),
            amplitude=max(0.1, min(0.95, self.amplitude * random.uniform(1.0 - amp_var, 1.0 + amp_var)))
        )
    
    def get_amplitude(self, time, duration):
        """Get the amplitude at a given time point"""
        if time < self.attack:
            # Attack phase
            return (time / self.attack) * self.amplitude
        elif time < self.attack + self.decay:
            # Decay phase
            decay_progress = (time - self.attack) / self.decay
            return self.amplitude * (1.0 - decay_progress * (1.0 - self.sustain))
        elif time < duration - self.release:
            # Sustain phase
            return self.amplitude * self.sustain
        else:
            # Release phase
            release_progress = (time - (duration - self.release)) / self.release
            return self.amplitude * self.sustain * (1.0 - release_progress)

class DrumSynthesizer:
    """Synthesizes various types of drum sounds"""
    
    def __init__(self, seed=None):
        """Initialize the synthesizer with optional random seed"""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
    def generate_kick(self, duration=0.5, envelope=None):
        """Generate a kick drum sound"""
        if envelope is None:
            envelope = Envelope(attack=0.001, decay=0.15, sustain=0.1, release=0.1, amplitude=0.9)
        
        # Randomize envelope
        env = envelope.randomize()
            
        # Create time array
        num_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, num_samples)
        
        # Randomly select synthesis method
        method = random.randint(0, 2)
        
        if method == 0:
            # Classic sine wave with pitch envelope
            start_freq = random.uniform(140, 160)
            end_freq = random.uniform(35, 45)
            freq_decay = random.uniform(0.06, 0.09)
            
            # Calculate frequency envelope
            freq_env = start_freq * np.exp(-t / freq_decay) + end_freq
            
            # Calculate phase by integrating frequency
            phase = 2 * np.pi * np.cumsum(freq_env) / SAMPLE_RATE
            
            # Generate sine wave
            samples = np.sin(phase)
            
        elif method == 1:
            # FM synthesis kick
            carrier_freq = random.uniform(50, 80)
            mod_freq = random.uniform(140, 180)
            mod_index = random.uniform(4, 8)
            index_decay = random.uniform(0.04, 0.08)
            
            # Calculate modulation index with decay
            mod_idx_env = mod_index * np.exp(-t / index_decay)
            
            # Generate carrier
            carrier_phase = 2 * np.pi * carrier_freq * t
            
            # Generate modulator
            mod_phase = 2 * np.pi * mod_freq * t
            modulator = np.sin(mod_phase)
            
            # Apply FM synthesis
            samples = np.sin(carrier_phase + mod_idx_env * modulator)
            
        else:
            # Layered oscillators with distortion
            fundamental_freq = random.uniform(45, 55)
            start_freq = random.uniform(160, 200)
            freq_decay = random.uniform(0.05, 0.08)
            
            # Generate fundamental with harmonics
            harmonics = [1.0, 0.5, 0.25, 0.125, 0.0625]
            fundamental = np.zeros_like(t)
            for i, strength in enumerate(harmonics):
                harmonic_freq = fundamental_freq * (i + 1)
                fundamental += strength * np.sin(2 * np.pi * harmonic_freq * t)
            fundamental /= sum(harmonics)
            
            # Generate click/attack
            click_freq = start_freq * np.exp(-t / freq_decay)
            click = np.sin(2 * np.pi * np.cumsum(click_freq) / SAMPLE_RATE) * np.exp(-t / 0.02)
            
            # Mix components
            samples = fundamental * 0.7 + click * 0.3
            
            # Apply distortion
            distortion_amount = random.uniform(1.5, 3.0)
            samples = np.tanh(samples * distortion_amount)
        
        # Apply amplitude envelope
        amplitude = np.array([env.get_amplitude(time, duration) for time in t])
        samples = samples * amplitude
        
        return samples
    
    def generate_snare(self, duration=0.4, envelope=None):
        """Generate a snare drum sound"""
        if envelope is None:
            envelope = Envelope(attack=0.001, decay=0.1, sustain=0.1, release=0.1, amplitude=0.8)
        
        # Randomize envelope
        env = envelope.randomize()
            
        # Create time array
        num_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, num_samples)
        
        # Randomly select synthesis method
        method = random.randint(0, 2)
        
        if method == 0:
            # Classic tone + noise snare
            tone_freq = random.uniform(170, 200)
            noise_mix = random.uniform(0.7, 0.9)
            
            # Generate tone component
            tone = np.sin(2 * np.pi * tone_freq * t)
            
            # Generate noise component
            noise_cutoff = random.uniform(2000, 4000)
            noise = np.zeros_like(t)
            for j in range(1, 6):
                noise_freq = noise_cutoff * j / 3.0
                noise_phase = 2 * np.pi * noise_freq * t + np.random.random() * 2 * np.pi
                noise += np.sin(noise_phase) / j
            
            # Normalize noise and apply random gain
            noise = noise / 5.0 * random.uniform(0.8, 1.2)
            
            # Mix tone and noise
            samples = noise * noise_mix + tone * (1 - noise_mix)
            
        elif method == 1:
            # Body + rattle snare
            body_freq = random.uniform(150, 180)
            rattle_freq = random.uniform(1000, 2500)
            rattle_decay = random.uniform(0.1, 0.2)
            
            # Generate body component
            body_phase = 2 * np.pi * body_freq * t
            body = np.sin(body_phase) * np.exp(-t / 0.1)
            
            # Generate rattle component
            rattle = np.zeros_like(t)
            for j in range(1, 9):
                granule_offset = 0.005 * j
                granule_t = t + granule_offset
                granule_env = np.exp(-(granule_t / rattle_decay))
                granule_phase = 2 * np.pi * rattle_freq * granule_t + np.random.random() * 2 * np.pi
                rattle += np.sin(granule_phase) * granule_env
            
            # Normalize and apply decay
            rattle = rattle / 8.0 * random.uniform(0.8, 1.2) * np.exp(-t / 0.15)
            
            # Mix body and rattle
            samples = body * 0.4 + rattle * 0.6
            
        else:
            # Layered noise snare with pitch bend
            resonant_freq = random.uniform(160, 220)
            resonant_decay = random.uniform(0.04, 0.08)
            noise_mix = random.uniform(0.6, 0.8)
            
            # Generate resonant component
            current_freq = resonant_freq * (1.0 - 0.5 * (1.0 - np.exp(-t / resonant_decay)))
            
            # Use a saw wave for the resonant component
            resonant = 2.0 * (((current_freq * t) % 1.0) - 0.5)
            
            # Generate noise component with bursts
            noise = np.zeros_like(t)
            for j in range(3):
                # Create burst offsets
                burst_offset = 0.01 * j
                burst_t = np.maximum(0, t - burst_offset)
                burst_env = np.exp(-burst_t / (0.1 * (j + 1)))
                noise += (np.random.random(num_samples) * 2 - 1) * burst_env
            
            # Apply soft clipping to noise
            noise = noise / (1.0 + 1.5 * np.abs(noise))
            
            # Mix resonant and noise components
            samples = noise * noise_mix + resonant * (1 - noise_mix)
        
        # Apply amplitude envelope
        amplitude = np.array([env.get_amplitude(time, duration) for time in t])
        samples = samples * amplitude
        
        return samples
    
    def generate_hihat(self, duration=0.2, envelope=None, is_open=False):
        """Generate a hi-hat sound"""
        if envelope is None:
            if is_open:
                envelope = Envelope(attack=0.001, decay=0.1, sustain=0.2, release=0.3, amplitude=0.7)
                duration = max(duration, 0.5)  # Ensure longer duration for open hats
            else:
                envelope = Envelope(attack=0.001, decay=0.05, sustain=0.0, release=0.05, amplitude=0.7)
                duration = min(duration, 0.2)  # Ensure shorter duration for closed hats
        
        # Randomize envelope
        env = envelope.randomize()
        
        # Create time array
        num_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, num_samples)
        
        # Randomly select synthesis method
        method = random.randint(0, 2)
        
        if method == 0:
            # Square wave resonators
            center_freq = random.uniform(7000, 10000)
            if not is_open:
                center_freq *= 1.2  # Higher frequency for closed hats
            
            # Generate multiple square waves at different frequencies
            num_oscillators = random.randint(5, 8)
            samples = np.zeros_like(t)
            
            for i in range(num_oscillators):
                freq_offset = random.uniform(0.9, 1.1)
                osc_freq = center_freq * freq_offset
                phase_offset = random.uniform(0, 2 * np.pi)
                osc_phase = 2 * np.pi * osc_freq * t + phase_offset
                # Square wave
                square = np.sign(np.sin(osc_phase))
                samples += square
            
            # Normalize
            samples = samples / num_oscillators
            
            # Add some noise
            noise = np.random.random(num_samples) * 2 - 1
            samples = samples * 0.7 + noise * 0.3
            
        elif method == 1:
            # FM metallic hihat
            carrier_freq = random.uniform(8000, 10000)
            if is_open:
                carrier_freq *= 0.9  # Slightly lower frequency for open hats
            
            mod_freq = random.uniform(7000, 8000)
            mod_index = random.uniform(3, 5)
            
            # FM synthesis
            mod_phase = 2 * np.pi * mod_freq * t
            modulator = np.sin(mod_phase)
            
            carrier_phase = 2 * np.pi * carrier_freq * t + mod_index * modulator
            samples = np.sin(carrier_phase)
            
            # Add some noise
            noise = np.random.random(num_samples) * 2 - 1
            samples = samples * 0.8 + noise * 0.2
            
            # Optional distortion
            if random.random() < 0.3:
                distortion_amount = random.uniform(1.0, 2.0)
                samples = samples / (1.0 + distortion_amount * np.abs(samples))
            
        else:
            # Filtered noise bursts
            cutoff_freq = random.uniform(6000, 10000)
            if not is_open:
                cutoff_freq *= 1.2  # Higher cutoff for closed hats
            
            resonance = random.uniform(1.0, 3.0)
            
            # Generate filtered noise
            samples = np.zeros_like(t)
            for j in range(1, 7):
                band_freq = cutoff_freq * j / (4 if is_open else 3)
                q = resonance / j
                
                # Simulated bandpass filter using sine oscillator to modulate noise
                band_phase = 2 * np.pi * band_freq * t
                band_osc = np.sin(band_phase)
                noise = np.random.random(num_samples) * 2 - 1
                
                samples += (noise * band_osc) / j
            
        # Apply amplitude envelope
        amplitude = np.array([env.get_amplitude(time, duration) for time in t])
        samples = samples * amplitude
        
        return samples
    
    def generate_crash(self, duration=2.0, envelope=None):
        """Generate a crash cymbal sound"""
        if envelope is None:
            envelope = Envelope(attack=0.001, decay=0.2, sustain=0.3, release=1.5, amplitude=0.8)
        
        # Randomize envelope
        env = envelope.randomize()
            
        # Create time array
        num_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, num_samples)
        
        # Randomly select synthesis method
        method = random.randint(0, 2)
        
        if method == 0:
            # Complex inharmonic oscillators
            base_freq = random.uniform(3800, 4200)
            num_oscillators = random.randint(18, 25)
            
            # Prime number ratios for inharmonicity
            prime_ratios = [1.0, 1.41, 1.73, 1.97, 2.11, 2.29, 2.53, 2.71, 2.97, 3.31]
            
            # Generate complex set of oscillators
            samples = np.zeros_like(t)
            for i in range(num_oscillators):
                freq_ratio = prime_ratios[i % len(prime_ratios)]
                random_offset = random.uniform(0.98, 1.02)
                freq = base_freq * freq_ratio * random_offset
                decay = random.uniform(0.8, 2.5) + (i * 0.1)
                phase_offset = random.uniform(0, 2 * np.pi)
                
                osc_phase = 2 * np.pi * freq * t + phase_offset
                osc_decay = np.exp(-t * decay)
                osc_signal = np.sin(osc_phase) * osc_decay * (1.0 / np.sqrt(i + 1))
                
                samples += osc_signal
            
            # Normalize
            samples = samples / np.sqrt(num_oscillators)
            
            # Add some noise
            noise = (np.random.random(num_samples) * 2 - 1) * np.exp(-t * 1.5)
            samples += noise
            
        elif method == 1:
            # FM synthesis with multiple modulators
            carrier_freq = random.uniform(3500, 4500)
            mod_freq1 = random.uniform(4000, 5000)
            mod_freq2 = random.uniform(3000, 4000)
            mod_index1 = random.uniform(3, 5)
            mod_index2 = random.uniform(2, 4)
            
            # Dynamic modulation indices with decay
            mod_idx1_env = mod_index1 * np.exp(-t / 0.5)
            mod_idx2_env = mod_index2 * np.exp(-t / 0.8)
            
            # First modulator
            mod1_phase = 2 * np.pi * mod_freq1 * t
            mod1_signal = np.sin(mod1_phase)
            
            # Second modulator
            mod2_phase = 2 * np.pi * mod_freq2 * t
            mod2_signal = np.sin(mod2_phase)
            
            # Carrier with combined modulation
            carrier_phase = 2 * np.pi * carrier_freq * t + mod_idx1_env * mod1_signal + mod_idx2_env * mod2_signal
            carrier_signal = np.sin(carrier_phase)
            
            # Add some noise
            noise = (np.random.random(num_samples) * 2 - 1) * np.exp(-t * 1.0)
            
            # Mix signals
            samples = carrier_signal * 0.8 + noise * 0.2
            
        else:
            # Noise burst with resonant filtering
            num_resonators = random.randint(15, 25)
            samples = np.zeros_like(t)
            
            # Create resonant filters
            for i in range(num_resonators):
                base_freq = random.uniform(3000, 5000)
                freq_mult = random.uniform(0.8, 1.2) * (1.0 + i * 0.1)
                freq = base_freq * freq_mult
                q = random.uniform(20, 50)
                phase_offset = random.uniform(0, 2 * np.pi)
                
                # Simulated resonant filter
                omega = 2 * np.pi * freq / SAMPLE_RATE
                decay = np.exp(-t * 2.0 / (q * 0.1))
                response_phase = omega * np.arange(num_samples) + phase_offset
                
                # Apply noise through the resonant filter
                noise = np.random.random(num_samples) * 2 - 1
                filtered = noise * np.sin(response_phase) * decay
                
                samples += filtered / num_resonators
            
            # Apply additional excitation at the beginning
            excitation = np.zeros_like(t)
            excitation_idx = np.where(t < 0.01)[0]
            excitation[excitation_idx] = (np.random.random(len(excitation_idx)) * 2 - 1) * np.exp(-t[excitation_idx] / 0.003) * 0.5
            samples += excitation
        
        # Apply amplitude envelope
        amplitude = np.array([env.get_amplitude(time, duration) for time in t])
        samples = samples * amplitude
        
        return samples
    
    def generate_tom(self, duration=0.5, envelope=None, pitch=1.0):
        """Generate a tom drum sound"""
        if envelope is None:
            envelope = Envelope(attack=0.001, decay=0.1, sustain=0.15, release=0.25, amplitude=0.8)
        
        # Randomize envelope
        env = envelope.randomize()
        
        # Apply pitch factor (with slight random variation)
        pitch_factor = pitch * random.uniform(0.95, 1.05)
            
        # Create time array
        num_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, num_samples)
        
        # Randomly select synthesis method
        method = random.randint(0, 2)
        
        if method == 0:
            # Sine wave with pitch envelope
            start_freq = 180.0 * pitch_factor * random.uniform(0.97, 1.03)
            end_freq = 60.0 * pitch_factor * random.uniform(0.95, 1.05)
            freq_decay = random.uniform(0.12, 0.18)
            
            # Calculate frequency envelope
            freq_env = start_freq * np.exp(-t / freq_decay) + end_freq
            
            # Calculate phase by integrating frequency
            phase = 2 * np.pi * np.cumsum(freq_env) / SAMPLE_RATE
            
            # Generate tone
            tone = np.sin(phase)
            
            # Add a small amount of noise
            noise = np.random.random(num_samples) * 2 - 1
            
            # Mix tone and noise
            samples = tone * 0.85 + noise * 0.15
            
        elif method == 1:
            # FM synthesis tom
            carrier_freq = 70.0 * pitch_factor
            mod_freq = 180.0 * pitch_factor
            mod_index = random.uniform(3.0, 5.0)
            index_decay = random.uniform(0.08, 0.12)
            
            # Calculate modulation index with decay
            mod_idx_env = mod_index * np.exp(-t / index_decay)
            
            # Generate modulator
            mod_phase = 2 * np.pi * mod_freq * t
            modulator = np.sin(mod_phase)
            
            # Generate carrier with FM
            carrier_phase = 2 * np.pi * carrier_freq * t + mod_idx_env * modulator
            samples = np.sin(carrier_phase)
            
        else:
            # Layered harmonics tom
            fundamental_freq = 80.0 * pitch_factor
            harmonic_decay = random.uniform(0.1, 0.2)
            
            # Create harmonic series
            num_harmonics = random.randint(3, 6)
            samples = np.zeros_like(t)
            
            for i in range(num_harmonics):
                harmonic_freq = fundamental_freq * (i + 1)
                harmonic_decay_rate = harmonic_decay / (i + 1)
                harmonic_env = np.exp(-t / harmonic_decay_rate)
                harmonic_phase = 2 * np.pi * harmonic_freq * t
                harmonic_signal = np.sin(harmonic_phase) * harmonic_env / (i + 1)
                
                samples += harmonic_signal
            
            # Normalize
            samples = samples / sum([1.0 / (i + 1) for i in range(num_harmonics)])
            
            # Add attack transient
            attack_idx = np.where(t < 0.02)[0]
            if len(attack_idx) > 0:
                click_freq = 400.0 * pitch_factor
                click_phase = 2 * np.pi * click_freq * t[attack_idx]
                click = np.sin(click_phase) * np.exp(-t[attack_idx] / 0.01)
                samples[attack_idx] += click * 0.3
            
        # Apply amplitude envelope
        amplitude = np.array([env.get_amplitude(time, duration) for time in t])
        samples = samples * amplitude
        
        return samples
    
    def generate_clap(self, duration=0.3, envelope=None):
        """Generate a clap sound"""
        if envelope is None:
            envelope = Envelope(attack=0.001, decay=0.05, sustain=0.3, release=0.2, amplitude=0.75)
        
        # Randomize envelope
        env = envelope.randomize()
            
        # Create time array
        num_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, num_samples)
        
        # Randomly select synthesis method
        method = random.randint(0, 2)
        
        if method == 0:
            # Classic multiple noise bursts clap
            center_freq = random.uniform(900, 1100)
            
            # Create multiple bursts of noise
            num_bursts = random.randint(3, 5)
            burst_times = [i * random.uniform(0.003, 0.007) for i in range(num_bursts)]
            burst_duration = random.uniform(0.015, 0.025)
            
            # Generate bursts
            samples = np.zeros_like(t)
            for burst_time in burst_times:
                burst_indices = np.where((t >= burst_time) & (t < burst_time + burst_duration))[0]
                if len(burst_indices) > 0:
                    local_t = t[burst_indices] - burst_time
                    burst_env = np.sin(np.pi * local_t / burst_duration)
                    burst_noise = (np.random.random(len(burst_indices)) * 2 - 1) * burst_env
                    samples[burst_indices] += burst_noise
            
            # Apply main envelope after the initial bursts
            burst_end_time = burst_times[-1] + burst_duration
            main_indices = np.where(t >= burst_end_time)[0]
            if len(main_indices) > 0:
                main_t = t[main_indices] - burst_end_time
                main_env = np.array([env.get_amplitude(time, duration - burst_end_time) for time in main_t])
                main_noise = (np.random.random(len(main_indices)) * 2 - 1) * main_env
                samples[main_indices] += main_noise
            
            # Apply bandpass filter (simplified)
            samples *= 0.8
            
        elif method == 1:
            # Filtered noise clap
            center_freq = random.uniform(1000, 1500)
            bandwidth = random.uniform(500, 800)
            
            # Start with noise
            noise = np.random.random(num_samples) * 2 - 1
            
            # Apply envelope with random variations
            amplitude = np.array([env.get_amplitude(time, duration) for time in t])
            
            # Add some random variations to simulate inconsistent hand clapping
            variation = np.ones_like(t)
            early_indices = np.where(t < 0.05)[0]
            if len(early_indices) > 0:
                variation[early_indices] += 0.5 * (np.random.random(len(early_indices)) * 2 - 1) * np.exp(-t[early_indices] / 0.01)
            
            # Generate filtered noise
            samples = np.zeros_like(t)
            for j in range(1, 5):
                band_freq = center_freq * j * random.uniform(0.9, 1.1)
                band_phase = 2 * np.pi * band_freq * t
                
                # Modulate noise with sine waves at filter frequencies
                band_signal = np.sin(band_phase) * noise
                samples += band_signal / j
            
            # Add transient attack
            attack_indices = np.where(t < 0.01)[0]
            if len(attack_indices) > 0:
                attack_noise = (np.random.random(len(attack_indices)) * 2 - 1) * np.exp(-t[attack_indices] / 0.002) * 0.5
                samples[attack_indices] += attack_noise
            
            # Apply amplitude envelope with variations
            samples = samples * amplitude * variation
            
        else:
            # Resonant body clap
            body_freq = random.uniform(800, 1200)
            resonance = random.uniform(5, 10)
            
            # Create a sequence of mini-attacks
            num_attacks = random.randint(4, 6)
            attack_times = [i * random.uniform(0.004, 0.008) for i in range(num_attacks)]
            
            # Generate resonant body sound
            body_phase = 2 * np.pi * body_freq * t
            body_signal = np.sin(body_phase) * np.exp(-t * resonance)
            
            # Generate attack transients
            samples = body_signal.copy()
            for attack_time in attack_times:
                attack_indices = np.where((t >= attack_time) & (t < attack_time + 0.01))[0]
                if len(attack_indices) > 0:
                    local_t = t[attack_indices] - attack_time
                    attack_env = np.exp(-local_t / 0.003)
                    attack_noise = (np.random.random(len(attack_indices)) * 2 - 1) * attack_env * 0.5
                    samples[attack_indices] += attack_noise
            
            # Add some noise to make it less pure
            noise = (np.random.random(num_samples) * 2 - 1) * np.exp(-t / 0.05)
            samples += noise
            
            # Apply amplitude envelope
            amplitude = np.array([env.get_amplitude(time, duration) for time in t])
            samples = samples * amplitude
        
        return samples
    
    def generate_rimshot(self, duration=0.25, envelope=None):
        """Generate a rimshot sound"""
        if envelope is None:
            envelope = Envelope(attack=0.001, decay=0.05, sustain=0.1, release=0.15, amplitude=0.8)
        
        # Randomize parameters (less variation for sharper sound)
        env = envelope.randomize(attack_var=0.05, decay_var=0.15, sustain_var=0.1, release_var=0.15, amp_var=0.1)
            
        # Create time array
        num_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, num_samples)
        
        # Rimshot consists of a click (stick hitting rim) and resonant body
        click_freq = random.uniform(1800, 2500)
        body_freq = random.uniform(350, 450)
        
        # Generate click component (very short high-frequency burst)
        click_phase = 2 * np.pi * click_freq * t
        click_env = np.exp(-t / 0.003)
        click = np.sin(click_phase) * click_env
        
        # Generate body component (mid-frequency tone)
        body_phase = 2 * np.pi * body_freq * t
        body_env = np.exp(-t / 0.1)
        body = np.sin(body_phase) * body_env
        
        # Add some noise for texture
        noise = (np.random.random(num_samples) * 2 - 1) * np.exp(-t / 0.02)
        
        # Mix all components
        samples = click * 0.6 + body * 0.3 + noise * 0.1
        
        # Apply amplitude envelope
        amplitude = np.array([env.get_amplitude(time, duration) for time in t])
        samples = samples * amplitude
        
        return samples
    
    def generate_cowbell(self, duration=0.4, envelope=None):
        """Generate a cowbell sound"""
        if envelope is None:
            envelope = Envelope(attack=0.001, decay=0.1, sustain=0.2, release=0.3, amplitude=0.75)
        
        # Randomize envelope
        env = envelope.randomize()
            
        # Create time array
        num_samples = int(duration * SAMPLE_RATE)
        t = np.linspace(0, duration, num_samples)
        
        # Cowbell consists of two main resonant frequencies
        freq1 = random.uniform(550, 650)  # Lower frequency
        freq2 = random.uniform(800, 900)  # Higher frequency
        
        # Generate tuned oscillators
        phase1 = 2 * np.pi * freq1 * t
        phase2 = 2 * np.pi * freq2 * t
        
        # Use square waves for characteristic metallic sound
        wave1 = np.sign(np.sin(phase1))
        wave2 = np.sign(np.sin(phase2))
        
        # Apply different decay rates to each oscillator
        env1 = np.exp(-t / 0.2)
        env2 = np.exp(-t / 0.15)
        
        # Mix waves
        samples = wave1 * env1 * 0.6 + wave2 * env2 * 0.4
        
        # Add initial attack click
        attack_indices = np.where(t < 0.01)[0]
        if len(attack_indices) > 0:
            click = (np.random.random(len(attack_indices)) * 2 - 1) * np.exp(-t[attack_indices] / 0.002) * 0.3
            samples[attack_indices] += click
        
        # Apply soft clipping for a slight distortion characteristic of metal
        samples = np.tanh(samples * 1.2)
        
        # Apply amplitude envelope
        amplitude = np.array([env.get_amplitude(time, duration) for time in t])
        samples = samples * amplitude
        
        return samples
    
    def save_to_wav(self, samples, filepath):
        """Save audio samples to a WAV file"""
        # Normalize to prevent clipping
        max_amp = np.max(np.abs(samples))
        if max_amp > 0:
            normalized = samples / max_amp * 0.95
        else:
            normalized = samples
        
        # Convert to 16-bit PCM
        samples_16bit = (normalized * 32767).astype(np.int16)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filepath)) or '.', exist_ok=True)
        
        # Save WAV file
        wavfile.write(filepath, SAMPLE_RATE, samples_16bit)
        print(f"File saved: {filepath}")


def generate_drum_sounds(synth, drum_type, output_dir=".", variations=3):
    """Generate variations of a specific drum type"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    if drum_type == "kick":
        # Generate kick variations
        base_env = Envelope(attack=0.001, decay=0.15, sustain=0.1, release=0.1, amplitude=0.9)
        
        for i in range(1, variations + 1):
            kick = synth.generate_kick(duration=random.uniform(0.4, 0.6), envelope=base_env)
            synth.save_to_wav(kick, f"{output_dir}/kick{i}.wav")
    
    elif drum_type == "snare":
        # Generate snare variations
        base_env = Envelope(attack=0.001, decay=0.1, sustain=0.1, release=0.1, amplitude=0.8)
        
        for i in range(1, variations + 1):
            snare = synth.generate_snare(duration=random.uniform(0.3, 0.5), envelope=base_env)
            synth.save_to_wav(snare, f"{output_dir}/snare{i}.wav")
    
    elif drum_type == "hihat":
        # Generate closed hi-hat variations
        closed_env = Envelope(attack=0.001, decay=0.05, sustain=0.0, release=0.05, amplitude=0.7)
        
        for i in range(1, variations + 1):
            hihat_closed = synth.generate_hihat(duration=random.uniform(0.1, 0.2), envelope=closed_env, is_open=False)
            synth.save_to_wav(hihat_closed, f"{output_dir}/hihat_closed{i}.wav")
        
        # Generate open hi-hat variations
        open_env = Envelope(attack=0.001, decay=0.1, sustain=0.2, release=0.3, amplitude=0.7)
        
        for i in range(1, variations + 1):
            hihat_open = synth.generate_hihat(duration=random.uniform(0.5, 0.7), envelope=open_env, is_open=True)
            synth.save_to_wav(hihat_open, f"{output_dir}/hihat_open{i}.wav")
    
    elif drum_type == "crash":
        # Generate crash cymbal variations
        base_env = Envelope(attack=0.001, decay=0.2, sustain=0.3, release=1.5, amplitude=0.8)
        
        for i in range(1, variations + 1):
            crash = synth.generate_crash(duration=random.uniform(1.8, 2.2), envelope=base_env)
            synth.save_to_wav(crash, f"{output_dir}/crash{i}.wav")
    
    elif drum_type == "tom":
        # Generate high tom variations
        high_env = Envelope(attack=0.001, decay=0.1, sustain=0.1, release=0.2, amplitude=0.75)
        
        for i in range(1, variations + 1):
            tom_high = synth.generate_tom(duration=random.uniform(0.3, 0.5), envelope=high_env, pitch=random.uniform(1.4, 1.6))
            synth.save_to_wav(tom_high, f"{output_dir}/tom_high{i}.wav")
        
        # Generate mid tom variations
        mid_env = Envelope(attack=0.001, decay=0.1, sustain=0.15, release=0.25, amplitude=0.8)
        
        for i in range(1, variations + 1):
            tom_mid = synth.generate_tom(duration=random.uniform(0.4, 0.6), envelope=mid_env, pitch=random.uniform(0.9, 1.1))
            synth.save_to_wav(tom_mid, f"{output_dir}/tom_mid{i}.wav")
        
        # Generate low tom variations
        low_env = Envelope(attack=0.001, decay=0.15, sustain=0.2, release=0.3, amplitude=0.85)
        
        for i in range(1, variations + 1):
            tom_low = synth.generate_tom(duration=random.uniform(0.5, 0.7), envelope=low_env, pitch=random.uniform(0.6, 0.8))
            synth.save_to_wav(tom_low, f"{output_dir}/tom_low{i}.wav")
    
    elif drum_type == "clap":
        # Generate clap variations
        base_env = Envelope(attack=0.001, decay=0.05, sustain=0.3, release=0.2, amplitude=0.75)
        
        for i in range(1, variations + 1):
            clap = synth.generate_clap(duration=random.uniform(0.25, 0.35), envelope=base_env)
            synth.save_to_wav(clap, f"{output_dir}/clap{i}.wav")
    
    elif drum_type == "rimshot":
        # Generate rimshot variations
        base_env = Envelope(attack=0.001, decay=0.05, sustain=0.1, release=0.15, amplitude=0.8)
        
        for i in range(1, variations + 1):
            rimshot = synth.generate_rimshot(duration=random.uniform(0.2, 0.3), envelope=base_env)
            synth.save_to_wav(rimshot, f"{output_dir}/rimshot{i}.wav")
    
    elif drum_type == "cowbell":
        # Generate cowbell variations
        base_env = Envelope(attack=0.001, decay=0.1, sustain=0.2, release=0.3, amplitude=0.75)
        
        for i in range(1, variations + 1):
            cowbell = synth.generate_cowbell(duration=random.uniform(0.3, 0.5), envelope=base_env)
            synth.save_to_wav(cowbell, f"{output_dir}/cowbell{i}.wav")
    
    else:
        print(f"Unknown drum type: {drum_type}")
        print("Available types: kick, snare, hihat, crash, tom, clap, rimshot, cowbell")
        return False
    
    return True


def generate_all_drum_sounds(synth, output_dir=".", variations=3):
    """Generate all drum sound types"""
    print("Generating all drum sounds...")
    
    drum_types = ["kick", "snare", "hihat", "crash", "tom", "clap", "rimshot", "cowbell"]
    for drum_type in drum_types:
        print(f"Generating {drum_type} sounds...")
        generate_drum_sounds(synth, drum_type, output_dir, variations)
    
    print(f"All drum sounds generated in {output_dir}")


def generate_drum_kit(synth, output_dir="."):
    """Generate a complete drum kit with appropriate naming"""
    print("Generating complete drum kit...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Kick drum
    kick_env = Envelope(attack=0.001, decay=0.15, sustain=0.1, release=0.1, amplitude=0.9)
    kick = synth.generate_kick(duration=0.5, envelope=kick_env)
    synth.save_to_wav(kick, f"{output_dir}/kick.wav")
    
    # Snare drum
    snare_env = Envelope(attack=0.001, decay=0.1, sustain=0.1, release=0.1, amplitude=0.8)
    snare = synth.generate_snare(duration=0.4, envelope=snare_env)
    synth.save_to_wav(snare, f"{output_dir}/snare.wav")
    
    # Rim shot
    rimshot_env = Envelope(attack=0.001, decay=0.05, sustain=0.1, release=0.15, amplitude=0.8)
    rimshot = synth.generate_rimshot(duration=0.25, envelope=rimshot_env)
    synth.save_to_wav(rimshot, f"{output_dir}/rimshot.wav")
    
    # Closed hi-hat
    hihat_closed_env = Envelope(attack=0.001, decay=0.05, sustain=0.0, release=0.05, amplitude=0.7)
    hihat_closed = synth.generate_hihat(duration=0.15, envelope=hihat_closed_env, is_open=False)
    synth.save_to_wav(hihat_closed, f"{output_dir}/hihat_closed.wav")
    
    # Open hi-hat
    hihat_open_env = Envelope(attack=0.001, decay=0.1, sustain=0.2, release=0.3, amplitude=0.7)
    hihat_open = synth.generate_hihat(duration=0.6, envelope=hihat_open_env, is_open=True)
    synth.save_to_wav(hihat_open, f"{output_dir}/hihat_open.wav")
    
    # Crash cymbal
    crash_env = Envelope(attack=0.001, decay=0.2, sustain=0.3, release=1.5, amplitude=0.8)
    crash = synth.generate_crash(duration=2.0, envelope=crash_env)
    synth.save_to_wav(crash, f"{output_dir}/crash.wav")
    
    # Toms (high, mid, low)
    tom_high_env = Envelope(attack=0.001, decay=0.1, sustain=0.1, release=0.2, amplitude=0.75)
    tom_high = synth.generate_tom(duration=0.4, envelope=tom_high_env, pitch=1.5)
    synth.save_to_wav(tom_high, f"{output_dir}/tom_high.wav")
    
    tom_mid_env = Envelope(attack=0.001, decay=0.1, sustain=0.15, release=0.25, amplitude=0.8)
    tom_mid = synth.generate_tom(duration=0.5, envelope=tom_mid_env, pitch=1.0)
    synth.save_to_wav(tom_mid, f"{output_dir}/tom_mid.wav")
    
    tom_low_env = Envelope(attack=0.001, decay=0.15, sustain=0.2, release=0.3, amplitude=0.85)
    tom_low = synth.generate_tom(duration=0.6, envelope=tom_low_env, pitch=0.7)
    synth.save_to_wav(tom_low, f"{output_dir}/tom_low.wav")
    
    # Clap
    clap_env = Envelope(attack=0.001, decay=0.05, sustain=0.3, release=0.2, amplitude=0.75)
    clap = synth.generate_clap(duration=0.3, envelope=clap_env)
    synth.save_to_wav(clap, f"{output_dir}/clap.wav")
    
    # Cowbell
    cowbell_env = Envelope(attack=0.001, decay=0.1, sustain=0.2, release=0.3, amplitude=0.75)
    cowbell = synth.generate_cowbell(duration=0.4, envelope=cowbell_env)
    synth.save_to_wav(cowbell, f"{output_dir}/cowbell.wav")
    
    print(f"Complete drum kit generated in {output_dir}")


def main():
    """Main function to parse arguments and run the synthesizer"""
    parser = argparse.ArgumentParser(description="DrumSynth - Command-line drum synthesizer")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate specific drum type")
    generate_parser.add_argument("type", help="Drum type to generate")
    generate_parser.add_argument("--output", "-o", default=".", help="Output directory")
    generate_parser.add_argument("--variations", "-v", type=int, default=3, help="Number of variations to generate")
    generate_parser.add_argument("--seed", "-s", type=int, help="Random seed for reproducible results")
    
    # All command
    all_parser = subparsers.add_parser("all", help="Generate all drum types")
    all_parser.add_argument("--output", "-o", default=".", help="Output directory")
    all_parser.add_argument("--variations", "-v", type=int, default=3, help="Number of variations to generate")
    all_parser.add_argument("--seed", "-s", type=int, help="Random seed for reproducible results")
    
    # Kit command
    kit_parser = subparsers.add_parser("kit", help="Generate a complete drum kit")
    kit_parser.add_argument("--output", "-o", default=".", help="Output directory")
    kit_parser.add_argument("--name", "-n", default=f"drumkit_{int(time.time())}", help="Name for the kit directory")
    kit_parser.add_argument("--seed", "-s", type=int, help="Random seed for reproducible results")
    
    args = parser.parse_args()
    
    # Create synthesizer with random seed
    if hasattr(args, 'seed') and args.seed is not None:
        synth = DrumSynthesizer(seed=args.seed)
        print(f"Using random seed: {args.seed}")
    else:
        # Generate a random seed and print it
        seed = int(time.time() * 1000) % 1000000
        synth = DrumSynthesizer(seed=seed)
        print(f"Using random seed: {seed} (use --seed {seed} to reproduce these exact sounds)")
    
    if args.command == "generate":
        generate_drum_sounds(synth, args.type, args.output, args.variations)
    
    elif args.command == "all":
        generate_all_drum_sounds(synth, args.output, args.variations)
    
    elif args.command == "kit":
        kit_dir = os.path.join(args.output, args.name)
        generate_drum_kit(synth, kit_dir)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
