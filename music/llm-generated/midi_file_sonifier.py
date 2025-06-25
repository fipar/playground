# file_sonifier.py
#
# A Python script to convert any file into a MIDI audio file.
# This process is known as data sonification.
#
# Author: Gemini
#
# Dependencies:
#   - midiutil: A pure Python library for creating MIDI files.
#     Install it using pip:
#     pip install midiutil
#
# How to Run:
#   python file_sonifier.py <input_file> <output_file.mid>
#
# Example:
#   python file_sonifier.py my_document.txt music_from_text.mid
#   python file_sonifier.py my_photo.jpg music_from_photo.mid

import argparse
from midiutil import MIDIFile

def get_musical_scale(scale_name='major'):
    """
    Returns a list of MIDI note offsets for a given scale.
    This helps make the output sound more traditionally "musical".
    """
    scales = {
        'major': [0, 2, 4, 5, 7, 9, 11],  # Major scale intervals
        'minor': [0, 2, 3, 5, 7, 8, 10],  # Natural Minor scale intervals
        'pentatonic': [0, 2, 4, 7, 9],     # Major Pentatonic scale
        'chromatic': list(range(12))      # All notes
    }
    return scales.get(scale_name.lower(), scales['major'])

def sonify_file(input_path, output_path, duration=0.25, base_octave=4, scale_name='major'):
    """
    Reads bytes from a file and maps them to MIDI notes to create a sonified audio file.

    Args:
        input_path (str): The path to the file to sonify.
        output_path (str): The path to save the output MIDI file.
        duration (float): The duration of each note in beats.
        base_octave (int): The starting octave for the musical notes (0-10).
        scale_name (str): The name of the musical scale to use for mapping.
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

    print("Generating MIDI sequence...")

    # --- How We Interpret the Bytes ---
    #
    # 1. Pitch (The Note): Each byte is a number from 0 to 255. We map this
    #    to a note in a musical scale (like C-Major) to make it sound more
    #    melodic. We use the modulo operator (%) to wrap the 256 possible
    #    byte values around the notes available in our chosen scale across
    #    several octaves.
    #
    # 2. Volume (Velocity): MIDI note velocity ranges from 0 (silent) to 127
    #    (loudest). We scale the byte's 0-255 value down to this 0-127 range.
    #    This means different bytes will produce notes of different volumes,
    #    creating a dynamic feel.
    #
    # 3. Duration: For this simple script, each note has a fixed duration. More
    #    complex scripts could map byte values to different durations.
    # ------------------------------------

    # Get the notes for the chosen musical scale
    scale_notes_offsets = get_musical_scale(scale_name)
    
    # Create a list of MIDI note numbers across a few octaves
    base_note = 12 * base_octave  # C4 is MIDI note 60
    notes_in_scale = []
    for octave in range(4): # Use 4 octaves for a decent range
        for offset in scale_notes_offsets:
            notes_in_scale.append(base_note + (12 * octave) + offset)

    num_notes = len(notes_in_scale)

    # Initialize the MIDIFile object
    # 1 track, 120 beats per minute (BPM)
    track = 0
    channel = 0
    time = 0  # Start at the beginning of the track
    tempo = 120
    
    MyMIDI = MIDIFile(1)  # One track
    MyMIDI.addTempo(track, time, tempo)

    # Iterate over each byte in the file and create a note
    for i, byte_val in enumerate(file_bytes):
        # Map byte to a note in our scale
        note_index = byte_val % num_notes
        pitch = notes_in_scale[note_index]
        
        # Map byte to volume (MIDI velocity)
        # We scale it to a reasonable range, e.g., 60-127, so notes aren't too quiet.
        min_velocity = 60
        max_velocity = 127
        velocity = int((byte_val / 255) * (max_velocity - min_velocity) + min_velocity)

        # Add the note to the MIDI track
        MyMIDI.addNote(track, channel, pitch, time, duration, velocity)

        # Move the "playhead" forward in time for the next note
        time += duration

    print(f"Writing MIDI file to: {output_path}")
    try:
        with open(output_path, "wb") as output_file:
            MyMIDI.writeFile(output_file)
        print("Sonification complete!")
    except Exception as e:
        print(f"An error occurred while writing the MIDI file: {e}")


def main():
    """Main function to parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Sonify any file by converting its bytes into a MIDI audio file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_file", help="The path to the file you want to sonify.")
    parser.add_argument("output_file", help="The path for the output .mid file.")
    parser.add_argument(
        "-d", "--duration", type=float, default=0.25,
        help="Duration of each note in beats (e.g., 0.25 for a 16th note at 120bpm). Default: 0.25"
    )
    parser.add_argument(
        "-s", "--scale", type=str, default="major",
        help="Musical scale to use (major, minor, pentatonic, chromatic). Default: major"
    )

    args = parser.parse_args()

    sonify_file(args.input_file, args.output_file, args.duration, scale_name=args.scale)


if __name__ == "__main__":
    main()

