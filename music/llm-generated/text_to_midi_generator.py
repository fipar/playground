import sys
import argparse
from midiutil import MIDIFile

# MIDI note numbers for pitch classes.
# This mapping assumes C4 = 60. The formula used later is:
# midi_note = pitch_class_val + (octave + 1) * 12
# This means C0 = 12, C-1 = 0 (which is the base for pitch_class_val 0-11)
PITCH_CLASSES = {
    'C': 0, 'B#': 0,
    'C#': 1, 'DB': 1,
    'D': 2,
    'D#': 3, 'EB': 3,
    'E': 4, 'FB': 4,
    'F': 5, 'E#': 5,
    'F#': 6, 'GB': 6,
    'G': 7,
    'G#': 8, 'AB': 8,
    'A': 9,
    'A#': 10, 'BB': 10,
    'B': 11, 'CB': 11, # CB is B, B is B
}

def note_name_to_midi(note_name_str):
    """Converts a note name (e.g., "C4", "F#3", "Db5") to a MIDI note number."""
    note_name_upper = note_name_str.upper() # e.g., "C2B", "D4S" (for sharp), "E3"

    accidental_offset = 0
    # The part of the string that will be processed for pitch letter and octave
    # after potentially stripping a 'b' or 's' suffix.
    core_note_part = note_name_upper

    # Check for trailing 'B' (flat) or 'S' (sharp) as per new syntax
    if note_name_upper.endswith('B'):
        accidental_offset = -1
        core_note_part = note_name_upper[:-1] # Remove 'B'
    elif note_name_upper.endswith('S'): # Added 'S' for sharp suffix for consistency
        accidental_offset = 1
        core_note_part = note_name_upper[:-1] # Remove 'S'

    # At this point, core_note_part should be like "C2", "DB3", "F#4" (standard forms)
    if not core_note_part: # Handles cases like input being just "b" or "s"
        raise ValueError(f"Invalid note format: '{note_name_str}'. Note part is empty after processing suffix.")

    try:
        # Octave is the last char of core_note_part
        octave = int(core_note_part[-1])
    except (ValueError, IndexError): # IndexError if core_note_part is too short (e.g. just "C" after stripping suffix from "Cb")
        raise ValueError(f"Invalid note format or missing octave in: '{note_name_str}'. Expected format like 'C4', 'Db3', 'E2b', 'F3s'.")

    # Pitch part is everything before the octave in core_note_part
    pitch_part = core_note_part[:-1]

    if not pitch_part:
        raise ValueError(f"Missing pitch class in note: '{note_name_str}'.")

    if pitch_part not in PITCH_CLASSES:
        raise ValueError(f"Unknown pitch class: '{pitch_part}' (from '{core_note_part}') in note '{note_name_str}'")

    base_pitch_class_val = PITCH_CLASSES[pitch_part]
    final_pitch_class_val = (base_pitch_class_val + accidental_offset + 12) % 12 # Apply suffix offset and normalize

    midi_note = final_pitch_class_val + (octave + 1) * 12
    if not (0 <= midi_note <= 127):
        raise ValueError(f"MIDI note {midi_note} for '{note_name_str}' is out of range (0-127).")
    return midi_note

def main():
    parser = argparse.ArgumentParser(description="Generate a MIDI file from a text-based note description read from stdin.")
    parser.add_argument("output_midi_file", help="Path to save the generated MIDI file.")
    args = parser.parse_args()

    input_lines = sys.stdin.readlines()

    if not input_lines:
        print("Error: No input provided to stdin.", file=sys.stderr)
        sys.exit(1)

    # --- Parse Configuration Lines (Measure and Tempo) ---
    measure_denominator = None
    tempo = 120 # Default tempo
    instrument_type = "piano" # Default instrument

    processed_config_lines = 0

    for i, line_content in enumerate(input_lines):
        line_content = line_content.strip().lower()
        if not line_content or line_content.startswith("#"):
            processed_config_lines +=1
            continue

        if line_content.startswith("measure:"):
            if measure_denominator is not None:
                print(f"Warning: Multiple 'measure:' lines found. Using the first one encountered.", file=sys.stderr)
            else:
                try:
                    val = int(line_content.split(":")[1].strip())
                    if val <= 0:
                        raise ValueError("Measure denominator must be positive.")
                    measure_denominator = val
                except (IndexError, ValueError) as e:
                    print(f"Error parsing measure line on input line {i+1}: {e}. Expected 'measure: <denominator>'.", file=sys.stderr)
                    sys.exit(1)
            processed_config_lines +=1
        elif line_content.startswith("tempo:"):
            try:
                val = int(line_content.split(":")[1].strip())
                if val <= 0:
                    raise ValueError("Tempo must be positive.")
                tempo = val # Override default tempo
            except (IndexError, ValueError) as e:
                print(f"Error parsing tempo line on input line {i+1}: {e}. Expected 'tempo: <number>'.", file=sys.stderr)
                sys.exit(1)
            processed_config_lines +=1
        elif line_content.startswith("instrument:"):
            val = line_content.split(":")[1].strip()
            if val in ["piano", "drums"]:
                instrument_type = val
            else:
                print(f"Warning on input line {i+1}: Unknown instrument type '{val}'. Using default '{instrument_type}'. Supported: piano, drums.", file=sys.stderr)
            processed_config_lines +=1
        # Stop looking for config if measure is found and line is not a recognized config line.
        # This assumes all config lines (measure, tempo, instrument) appear before note data.
        # 'measure:' is mandatory, so we wait for it.
        elif measure_denominator is not None and not (line_content.startswith("tempo:") or line_content.startswith("instrument:")):
            break 
        elif i > 5 and measure_denominator is None: # Heuristic: if no measure after few lines, assume error
            print("Error: 'measure:' line not found near the beginning of the input.", file=sys.stderr)
            sys.exit(1)

    if measure_denominator is None:
        print("Error: 'measure: <denominator>' line is required in the input.", file=sys.stderr)
        sys.exit(1)

    unit_duration_qn = 4.0 / measure_denominator

    # --- MIDI Setup ---
    mf = MIDIFile(1)
    track = 0
    channel = 0 # Default to piano channel
    volume = 100 

    mf.addTempo(track, 0, tempo)

    if instrument_type == "drums":
        channel = 9 # Standard MIDI channel for drums
        # No specific program change needed for drums usually
    elif instrument_type == "piano":
        mf.addProgramChange(track, channel, 0, 0) # Program 0: Acoustic Grand Piano

    # --- Parse Note Lines ---
    for line_num, line_content in enumerate(input_lines[processed_config_lines:], start=processed_config_lines + 1):
        line_content = line_content.strip()
        if not line_content or line_content.startswith("#"):
            continue

        parts = line_content.split()
        if not (3 <= len(parts) <= 4):
            print(f"Error on input line {line_num}: Expected 3 or 4 parts (position note duration_multiplier [volume_offset]), got {len(parts)}: '{line_content}'", file=sys.stderr)   
            continue
        
        try:
            position_str = parts[0]
            position = float(position_str) # Parse position as a float
            note_name = parts[1]
            duration_multiplier = int(parts[2])
            note_specific_volume = volume # Start with default volume

            if duration_multiplier <= 0:
                raise ValueError("Duration multiplier must be positive.")

            if len(parts) == 4:
                volume_offset_str = parts[3]
                try:
                    volume_offset = int(volume_offset_str)
                    note_specific_volume = volume + volume_offset
                    # Clamp volume to MIDI range 0-127
                    note_specific_volume = max(0, min(127, note_specific_volume))
                except ValueError:
                    raise ValueError(f"Invalid volume offset '{volume_offset_str}'. Must be an integer.")
            
            # Position validation (can be done after parsing as float)
            if position <= 0:
                raise ValueError("Position must be positive and 1-indexed (can be fractional e.g., 1.0, 2.5).")
                
            midi_pitch = note_name_to_midi(note_name)
            
            start_time_qn = (position - 1) * unit_duration_qn
            note_duration_qn = duration_multiplier * unit_duration_qn
            
            mf.addNote(track, channel, midi_pitch, start_time_qn, note_duration_qn, note_specific_volume)

        except ValueError as e:
            print(f"Error on input line {line_num} ('{line_content}'): {e}", file=sys.stderr)
            continue
            
    try:
        with open(args.output_midi_file, "wb") as output_file_handle:
            mf.writeFile(output_file_handle)
        print(f"MIDI file '{args.output_midi_file}' generated successfully.")
    except IOError:
        print(f"Error: Could not write to MIDI file '{args.output_midi_file}'.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()