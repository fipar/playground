#!/usr/bin/env python3
import argparse
import numpy as np
import scipy.io.wavfile as wavfile
import random
import math

def generate_speech(duration=10, consonant_percentage=0.3, wpm=20, gender_gradient=0):
    """
    Generate synthetic speech-like audio with specified parameters.
    
    Args:
        duration: Length of audio in seconds
        consonant_percentage: Ratio of consonants to vowels (0-1)
        wpm: Words per minute
        gender_gradient: 0=male, 1=female, values in between are mix
    """
    sample_rate = 44100
    total_samples = int(duration * sample_rate)
    
    # Calculate timing based on WPM
    # Assuming average word length of 5 characters + 1 space
    chars_per_second = (wpm * 6) / 60
    phoneme_duration = 0.15  # Average phoneme duration in seconds
    silence_duration = 0.05  # Pause between words
    
    # Generate base frequencies for male/female voices
    male_base_freq = 120  # Hz
    female_base_freq = 220  # Hz
    base_freq = male_base_freq + (female_base_freq - male_base_freq) * gender_gradient
    
    # Formant frequencies for vowel-like and consonant-like sounds
    vowel_formants = [
        [730, 1090, 2440],  # 'a' like
        [270, 2290, 3010],  # 'i' like  
        [300, 870, 2240],   # 'u' like
        [530, 1840, 2480],  # 'e' like
        [570, 840, 2410]    # 'o' like
    ]
    
    consonant_formants = [
        [200, 1600, 2500],  # fricative-like
        [150, 800, 2200],   # stop-like
        [300, 1200, 2800],  # nasal-like
        [250, 1400, 2600],  # liquid-like
    ]
    
    # Initialize audio array
    audio = np.zeros(total_samples)
    
    # Generate speech patterns
    current_sample = 0
    word_pitch_multiplier = 1.0  # Track pitch variation across words
    phonemes_in_word = 0
    phonemes_per_word = random.randint(2, 6)  # Random word length

    while current_sample < total_samples:
        # Start a new word - set new pitch and intonation
        if phonemes_in_word == 0:
            # Random pitch variation between words (-20% to +20%)
            word_pitch_multiplier = random.uniform(0.8, 1.2)
            phonemes_per_word = random.randint(2, 6)

            # Add prosodic patterns: some words rise, some fall
            word_intonation_pattern = random.choice(['rise', 'fall', 'flat'])

        # Determine if this should be a consonant or vowel
        is_consonant = random.random() < consonant_percentage

        # Select formants
        if is_consonant:
            formants = random.choice(consonant_formants)
            phoneme_len = int(phoneme_duration * 0.7 * sample_rate)  # Consonants are shorter
        else:
            formants = random.choice(vowel_formants)
            phoneme_len = int(phoneme_duration * sample_rate)

        # Ensure we don't exceed the total duration
        if current_sample + phoneme_len > total_samples:
            phoneme_len = total_samples - current_sample

        # Generate the phoneme
        t = np.linspace(0, phoneme_len / sample_rate, phoneme_len)

        # Calculate intonation within the word
        progress_in_word = phonemes_in_word / max(1, phonemes_per_word - 1)
        if word_intonation_pattern == 'rise':
            intonation_mult = 1.0 + 0.15 * progress_in_word  # Rise up to 15%
        elif word_intonation_pattern == 'fall':
            intonation_mult = 1.0 - 0.15 * progress_in_word  # Fall down to 15%
        else:
            intonation_mult = 1.0

        # Create fundamental frequency with micro-variation and word-level pitch
        micro_variation = 1 + 0.05 * np.sin(2 * np.pi * 5 * t)  # 5 Hz micro-vibrato
        fundamental = base_freq * word_pitch_multiplier * intonation_mult * micro_variation
        
        # Generate formant-filtered sound
        phoneme_sound = np.zeros(phoneme_len)
        
        # Add fundamental and harmonics with formant filtering
        for harmonic in range(1, 6):
            harmonic_freq = fundamental * harmonic
            
            # Apply formant filtering (simple approximation)
            formant_strength = 0
            for formant_freq in formants:
                # Gaussian-like formant response
                formant_strength += np.exp(-((harmonic_freq.mean() - formant_freq) / (formant_freq * 0.2))**2)
            
            formant_strength = max(0.1, min(1.0, formant_strength))
            amplitude = (1.0 / harmonic) * formant_strength * 0.3
            
            phoneme_sound += amplitude * np.sin(2 * np.pi * harmonic_freq * t)
        
        # Apply amplitude envelope (attack, sustain, decay)
        envelope_attack = int(0.02 * sample_rate)  # 20ms attack
        envelope_decay = int(0.05 * sample_rate)   # 50ms decay
        
        envelope = np.ones(phoneme_len)
        
        if phoneme_len > envelope_attack:
            envelope[:envelope_attack] = np.linspace(0, 1, envelope_attack)
        if phoneme_len > envelope_decay:
            envelope[-envelope_decay:] = np.linspace(1, 0, envelope_decay)
            
        phoneme_sound *= envelope
        
        # Add to main audio
        audio[current_sample:current_sample + phoneme_len] += phoneme_sound
        current_sample += phoneme_len

        # Track phonemes in current word
        phonemes_in_word += 1

        # Add silence at word boundaries
        if phonemes_in_word >= phonemes_per_word:
            silence_len = int(silence_duration * sample_rate)
            current_sample += min(silence_len, total_samples - current_sample)
            phonemes_in_word = 0  # Start new word
    
    # Normalize audio
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio)) * 0.8
    
    # Apply gentle filtering to make it sound more natural
    from scipy import signal
    b, a = signal.butter(4, [80, 8000], btype='band', fs=sample_rate)
    audio = signal.filtfilt(b, a, audio)
    
    return audio.astype(np.float32), sample_rate

def main():
    parser = argparse.ArgumentParser(description='Generate synthetic speech-like audio')
    parser.add_argument('--duration', type=float, default=10, 
                      help='Duration in seconds (default: 10)')
    parser.add_argument('--consonant-percentage', type=float, default=0.3,
                      help='Consonant percentage 0-1 (default: 0.3)')
    parser.add_argument('--wpm', type=int, default=20,
                      help='Words per minute (default: 20)')
    parser.add_argument('--gender-gradient', type=float, default=0,
                      help='Gender gradient: 0=male, 1=female (default: 0)')
    parser.add_argument('--output', type=str, default='speech.wav',
                      help='Output filename (default: speech.wav)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.consonant_percentage < 0 or args.consonant_percentage > 1:
        print("Error: consonant-percentage must be between 0 and 1")
        return 1
    
    if args.gender_gradient < 0 or args.gender_gradient > 1:
        print("Error: gender-gradient must be between 0 and 1")
        return 1
    
    if args.duration <= 0:
        print("Error: duration must be positive")
        return 1
        
    if args.wpm <= 0:
        print("Error: wpm must be positive")
        return 1
    
    print(f"Generating {args.duration}s of synthetic speech...")
    print(f"Parameters: {args.consonant_percentage*100:.1f}% consonants, {args.wpm} WPM, gender={args.gender_gradient}")
    
    # Generate the audio
    audio, sample_rate = generate_speech(
        duration=args.duration,
        consonant_percentage=args.consonant_percentage,
        wpm=args.wpm,
        gender_gradient=args.gender_gradient
    )
    
    # Save to WAV file
    wavfile.write(args.output, sample_rate, (audio * 32767).astype(np.int16))
    print(f"Saved to {args.output}")
    
    return 0

if __name__ == '__main__':
    exit(main())