# wav_sonifier.py
#
# A Python script to convert any file into a WAV audio file.
# This script generates a raw audio waveform, mapping each byte of
# the input file to a specific audio frequency.
#
# Author: Gemini
#
# Dependencies:
#   None! This script uses only Python's standard libraries.
#
# How to Run:
#   python wav_sonifier.py <input_file> <output_file.wav>
#
# Example:
#   python wav_sonifier.py my_document.txt audio_from_text.wav
#   python wav_sonifier.py my_photo.jpg audio_from_photo.wav

import argparse
import math
import wave
import struct

def sonify_to_wav(input_path, output_path, duration_per_byte=0.05, sample_rate=44100):
    """
    Reads bytes from a file and maps them to sine wave frequencies to create a WAV audio file.

    Args:
        input_path (str): The path to the file to sonify.
        output_path (str): The path to save the output WAV file.
        duration_per_byte (float): The duration of the tone for each byte in seconds.
        sample_rate (int): The sample rate for the WAV file (e.g., 44100 for CD quality).
    """
    print(f"Reading file: {input_path}")
    try:
        with open(input_path, 'rb') as f:
            file_bytes = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'")
        return
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return

    print("Generating WAV file data...")

    # --- How We Interpret the Bytes ---
    #
    # 1. Frequency (Pitch): Each byte is a number from 0 to 255. We map this
    #    linearly to a frequency range. A low byte value (like 10) will produce
    #    a low-pitched tone, and a high byte value (like 250) will produce a
    #    high-pitched tone. We'll use a range of 200 Hz to 1200 Hz.
    #
    # 2. Waveform: For each frequency, we generate a pure sine wave. This is
    #    the most basic building block of sound.
    #
    # 3. Amplitude (Volume): For this script, we'll use a constant amplitude.
    #    This is the "loudness" of the wave. For 16-bit audio, the range is
    #    -32767 to 32767. We use a slightly lower value to prevent clipping.
    # ------------------------------------
    
    # WAV file parameters
    n_channels = 1  # Mono
    samp_width = 2  # 16-bit audio
    
    min_freq = 200.0
    max_freq = 1200.0
    amplitude = 32000 # Max for 16-bit is 32767

    # This will hold the raw audio data (frames)
    wav_frames = []
    
    # Iterate through each byte and generate a corresponding tone
    for byte_val in file_bytes:
        # Map the byte value (0-255) to a frequency
        frequency = min_freq + (byte_val / 255.0) * (max_freq - min_freq)

        # Calculate the number of frames for this tone's duration
        num_frames_for_byte = int(duration_per_byte * sample_rate)

        # Generate the sine wave for this byte
        for i in range(num_frames_for_byte):
            # Calculate the value of the wave at this sample point
            sample_value = math.sin(2 * math.pi * frequency * (i / sample_rate))
            
            # Scale it to our amplitude
            frame = int(sample_value * amplitude)
            
            # Pack the frame into a 16-bit signed integer (binary format)
            # 'h' is the format specifier for a short integer
            packed_frame = struct.pack('h', frame)
            wav_frames.append(packed_frame)

    # Join all the packed frames into a single byte string
    frames_data = b''.join(wav_frames)

    # Write the data to a WAV file
    print(f"Writing WAV file to: {output_path}")
    try:
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(n_channels)
            wav_file.setsampwidth(samp_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(frames_data)
        print("Sonification complete!")
    except Exception as e:
        print(f"An error occurred while writing the WAV file: {e}")

def main():
    """Main function to parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sonify any file by converting its bytes into a WAV audio file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_file", help="The path to the file you want to sonify.")
    parser.add_argument("output_file", help="The path for the output .wav file.")
    parser.add_argument(
        "-d", "--duration", type=float, default=0.05,
        help="Duration of the tone for each byte, in seconds. Default: 0.05"
    )

    args = parser.parse_args()

    sonify_to_wav(args.input_file, args.output_file, args.duration)

if __name__ == "__main__":
    main()

