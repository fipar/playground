import random
from midiutil import MIDIFile

def generate_mixolydian_bass_only_midi(filename="bb_mixolydian_bass_line.mid"):
    # Scale definition (used to guide the bass line's root notes)
    bb_mixolydian_base_midi = [58, 60, 62, 63, 65, 67, 68]  # Bb3, C4, D4, Eb4, F4, G4, Ab4
    scale_midi_abs = []
    for i in range(3): # Create 3 octaves of the scale
        for note in bb_mixolydian_base_midi:
            scale_midi_abs.append(note + 12 * i)
    
    # The melodic contour the bass follows uses this range
    melody_range_scale = scale_midi_abs[0:14+1] # Bb3 to Bb5 inclusive (15 notes)

    # MIDI parameters
    track = 0 # Single track for the bass
    channel = 0 # Single channel
    tempo = 100
    bass_volume = 105 

    mf = MIDIFile(1)  # One track
    mf.addTempo(track, 0, tempo)
    mf.addProgramChange(track, channel, 0, 32) # Program 32: Acoustic Bass

    current_time = 0.0
    # current_scale_idx determines the root note the bass will play (from the imaginary melody)
    current_scale_idx = 0 
    num_events = 120 # Total number of bass notes

    # Melodic phases for the contour that the bass line follows
    phases = [
        (len(melody_range_scale) - 1, 1),  # Ascend to Bb5
        (0, -1),                           # Descend to Bb3
        (len(melody_range_scale) // 2, 1), # Ascend to Bb4 (middle)
        (0, -1)                            # Descend to Bb3
    ]
    current_phase_idx = 0
    target_idx, direction = phases[current_phase_idx]

    for _ in range(num_events):
        # Determine next scale index for the imaginary melody
        rand_motion = random.random()
        step_size = 0
        if rand_motion < 0.75: # Normal step
            step_size = direction
        elif rand_motion < 0.90: # Jump a scale step
            step_size = 2 * direction
        else: # Repeat current note index (effectively step_size = 0 for index change)
            step_size = 0

        next_scale_idx = current_scale_idx + step_size
        
        # Boundary checks and phase progression for the imaginary melody
        if direction == 1 and next_scale_idx >= target_idx:
            next_scale_idx = target_idx
            current_phase_idx = (current_phase_idx + 1) % len(phases)
            target_idx, direction = phases[current_phase_idx]
        elif direction == -1 and next_scale_idx <= target_idx:
            next_scale_idx = target_idx
            current_phase_idx = (current_phase_idx + 1) % len(phases)
            target_idx, direction = phases[current_phase_idx]
        
        current_scale_idx = max(0, min(len(melody_range_scale) - 1, next_scale_idx))
        
        # This is the root note from the imaginary melody's current position
        melodic_root_pitch = melody_range_scale[current_scale_idx]
        
        # Determine duration for the bass note
        duration_choices = [0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.5] # Weighted towards 1.0
        duration = random.choice(duration_choices)

        # --- Calculate Bass Line Note ---
        bass_note_pitch = melodic_root_pitch - 12 # Start one octave down
        if bass_note_pitch > 50: # If still higher than approx D3 (MIDI 50)
            bass_note_pitch -= 12 # Go down another octave
        bass_note_pitch = max(28, bass_note_pitch) # Ensure it's not below E1 (MIDI 28)
        
        # Add the bass note to the track
        mf.addNote(track, channel, bass_note_pitch, current_time, duration, bass_volume)
            
        current_time += duration

    with open(filename, "wb") as output_file:
        mf.writeFile(output_file)
    print(f"MIDI file '{filename}' (bass line only) generated successfully.")

# Generate the MIDI file
generate_mixolydian_bass_only_midi()
