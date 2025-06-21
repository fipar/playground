#!/usr/bin/env python3

import sys
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import math

# --- Configuration ---
# This constant defines the maximum fade duration (in milliseconds) that the cut angle can produce.
# A 0-degree cut (most acute, theoretically) would result in this fade duration.
# A 45-degree cut results in half this duration.
# A 90-degree cut results in no fade.
MAX_FADE_EFFECT_MS = 50.0

def parse_line(line_number, line_content):
    """
    Parses a single line from the input file.
    Returns a dictionary with parsed data or None if parsing fails.
    """
    parts = line_content.split()
    if not (4 <= len(parts) <= 5):
        print(f"Warning: Line {line_number}: Incorrect number of fields. Expected 4 or 5, got {len(parts)}. Skipping.", file=sys.stderr)
        return None

    try:
        filename = parts[0]
        start_s = float(parts[1])
        duration_s = float(parts[2])
        outputstart_s = float(parts[3])
        
        cut_angle_deg = 90.0  # Default cut angle
        if len(parts) == 5:
            cut_angle_deg = float(parts[4])

        # Validate inputs
        if start_s < 0:
            print(f"Warning: Line {line_number}: Start time ({start_s}s) cannot be negative. Skipping.", file=sys.stderr)
            return None
        if duration_s <= 0:
            print(f"Warning: Line {line_number}: Duration ({duration_s}s) must be positive. Skipping.", file=sys.stderr)
            return None
        if outputstart_s < 0:
            print(f"Warning: Line {line_number}: Output start time ({outputstart_s}s) cannot be negative. Skipping.", file=sys.stderr)
            return None
            
        return {
            "filename": filename,
            "start_ms": start_s * 1000,
            "duration_ms": duration_s * 1000,
            "outputstart_ms": outputstart_s * 1000,
            "cut_angle_deg": cut_angle_deg,
            "line_number": line_number
        }
    except ValueError as e:
        print(f"Warning: Line {line_number}: Error parsing numerical values ({e}). Skipping.", file=sys.stderr)
        return None

def main():
    """
    Main function to process audio segments and generate the output file.
    """
    processed_segments_info = []
    max_output_end_time_ms = 0.0

    print("Starting audio processing...", file=sys.stderr)

    for i, line_raw in enumerate(sys.stdin):
        line_num = i + 1
        line = line_raw.strip()

        # Ignore blank lines and comments
        if not line or line.startswith('#'):
            continue

        parsed_data = parse_line(line_num, line)
        if not parsed_data:
            continue

        filename = parsed_data["filename"]
        start_ms = parsed_data["start_ms"]
        duration_ms = parsed_data["duration_ms"]
        outputstart_ms = parsed_data["outputstart_ms"]
        cut_angle_deg = parsed_data["cut_angle_deg"]

        print(f"Processing line {line_num}: file='{filename}', start={start_ms/1000:.2f}s, dur={duration_ms/1000:.2f}s, out_start={outputstart_ms/1000:.2f}s, angle={cut_angle_deg}deg", file=sys.stderr)

        try:
            audio_file = AudioSegment.from_file(filename)
        except FileNotFoundError:
            print(f"Error: Line {line_num}: Audio file '{filename}' not found. Skipping.", file=sys.stderr)
            continue
        except CouldntDecodeError:
            print(f"Error: Line {line_num}: Could not decode audio file '{filename}'. Ensure FFmpeg is installed and the file is a valid audio format. Skipping.", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Error: Line {line_num}: Loading audio file '{filename}' failed: {e}. Skipping.", file=sys.stderr)
            continue
        
        # Ensure slice start is within bounds
        if start_ms >= len(audio_file):
            print(f"Warning: Line {line_num}: Start time ({start_ms/1000:.2f}s) is at or beyond the duration of '{filename}' ({len(audio_file)/1000:.2f}s). Skipping segment.", file=sys.stderr)
            continue
        
        # Calculate actual duration to extract, capped by file length
        actual_duration_ms = min(duration_ms, len(audio_file) - start_ms)
        
        if actual_duration_ms <= 0:
             print(f"Warning: Line {line_num}: Calculated effective duration for '{filename}' is zero or negative. Skipping segment.", file=sys.stderr)
             continue

        segment = audio_file[start_ms : start_ms + actual_duration_ms]

        # Apply fade based on cut_angle
        fade_duration_ms = 0.0
        if not (0 < cut_angle_deg <= 90.0):
            if cut_angle_deg != 90.0: # Only warn if it's not the default or explicitly 90 but invalid
                 print(f"Info: Line {line_num}: Cut angle {cut_angle_deg}deg is outside the effective range (0 < angle <= 90). Treating as 90 degrees (no fade).", file=sys.stderr)
            # No fade for angles outside (0, 90] or exactly 90
        elif cut_angle_deg < 90.0: # 0 < cut_angle_deg < 90
            fade_ratio = (90.0 - cut_angle_deg) / 90.0
            fade_duration_ms = MAX_FADE_EFFECT_MS * fade_ratio
        
        if fade_duration_ms > 0:
            actual_segment_len_ms = len(segment)
            if actual_segment_len_ms == 0:
                print(f"Warning: Line {line_num}: Segment from '{filename}' has zero length after slicing. Skipping fade.", file=sys.stderr)
            else:
                # Ensure fade is not longer than half the segment length
                effective_fade_ms = min(fade_duration_ms, actual_segment_len_ms / 2.0)
                if effective_fade_ms > 0.5: # Apply if fade is at least somewhat significant
                    print(f"Info: Line {line_num}: Applying {int(round(effective_fade_ms))}ms fade-in/out for angle {cut_angle_deg}deg.", file=sys.stderr)
                    segment = segment.fade_in(duration=int(round(effective_fade_ms))).fade_out(duration=int(round(effective_fade_ms)))
                else:
                    print(f"Info: Line {line_num}: Calculated fade ({effective_fade_ms:.2f}ms) too short for angle {cut_angle_deg}deg. No fade applied.", file=sys.stderr)
        
        processed_segments_info.append({
            "segment": segment,
            "outputstart_ms": outputstart_ms,
            "line_num": line_num
        })
        
        current_segment_end_time_ms = outputstart_ms + len(segment)
        if current_segment_end_time_ms > max_output_end_time_ms:
            max_output_end_time_ms = current_segment_end_time_ms

    if not processed_segments_info:
        print("No valid audio segments processed. Output file 'output.wav' will not be generated.", file=sys.stderr)
        return

    print(f"All lines processed. Total output duration will be: {max_output_end_time_ms / 1000.0:.2f}s.", file=sys.stderr)
    
    # Ensure duration is an integer for AudioSegment.silent
    final_output_duration_ms = int(round(max_output_end_time_ms))
    if final_output_duration_ms <= 0:
         print("Warning: Final output duration is zero. 'output.wav' will be empty or not generated correctly.", file=sys.stderr)
         # Create a minimal silent segment if needed by export, or handle as Pydub prefers
         output_audio = AudioSegment.empty() 
    else:
        output_audio = AudioSegment.silent(duration=final_output_duration_ms)


    for info in processed_segments_info:
        print(f"Overlaying segment from line {info['line_num']} at {info['outputstart_ms']/1000:.2f}s.", file=sys.stderr)
        output_audio = output_audio.overlay(info["segment"], position=int(round(info["outputstart_ms"])))

    try:
        output_audio.export("output.wav", format="wav")
        print("Successfully generated output.wav", file=sys.stdout) # Final confirmation to stdout
    except Exception as e:
        print(f"Error exporting output.wav: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
