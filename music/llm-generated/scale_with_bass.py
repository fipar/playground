import random
from midiutil import MIDIFile

def generate_mixolydian_with_bass_midi(filename="bb_mixolydian_melody_with_bass.mid"):
    # Scale and MIDI setup
    bb_mixolydian_base_midi = [58, 60, 62, 63, 65, 67, 68]  # Bb3, C4, D4, Eb4, F4, G4, Ab4
    scale_midi_abs = []
    for i in range(3): # Create 3 octaves of the scale starting from Bb3
        for note in bb_mixolydian_base_midi:
            scale_midi_abs.append(note + 12 * i)
    
    melody_range_scale = scale_midi_abs[0:14+1] # Bb3 to Bb5 inclusive (15 notes)

    triads_info_map = {
        0: {"name": "Bb Maj", "type": "major", "intervals": [0, 4, 7]},
        1: {"name": "C min", "type": "minor", "intervals": [0, 3, 7]},
        2: {"name": "D dim", "type": "diminished", "intervals": [0, 3, 6]}, # Skipped
        3: {"name": "Eb Maj", "type": "major", "intervals": [0, 4, 7]},
        4: {"name": "F min", "type": "minor", "intervals": [0, 3, 7]},
        5: {"name": "G min", "type": "minor", "intervals": [0, 3, 7]},
        6: {"name": "Ab Maj", "type": "major", "intervals": [0, 4, 7]}
    }

    # MIDI parameters
    melody_track = 0
    bass_track = 1
    melody_channel = 0
    bass_channel = 1
    tempo = 100
    melody_volume = 100
    bass_volume = 105 # Slightly louder bass for foundation

    mf = MIDIFile(2)  # Two tracks
    mf.addTempo(melody_track, 0, tempo) # Tempo on track 0, applies to all
    mf.addTempo(bass_track, 0, tempo)   # Also add to other tracks for some players

    # Melody track (Acoustic Grand Piano)
    mf.addProgramChange(melody_track, melody_channel, 0, 0)
    # Bass track (Acoustic Bass)
    mf.addProgramChange(bass_track, bass_channel, 0, 32)


    current_time = 0.0
    current_scale_idx = 0 # Start at Bb3 for melody
    num_events = 120

    phases = [
        (len(melody_range_scale) - 1, 1),
        (0, -1),
        (len(melody_range_scale) // 2, 1),
        (0, -1)
    ]
    current_phase_idx = 0
    target_idx, direction = phases[current_phase_idx]

    for _ in range(num_events):
        rand_motion = random.random()
        step_size = 0
        if rand_motion < 0.75:
            step_size = direction
        elif rand_motion < 0.90:
            step_size = 2 * direction
        else:
            step_size = 0

        next_scale_idx = current_scale_idx + step_size
        
        if direction == 1 and next_scale_idx >= target_idx:
            next_scale_idx = target_idx
            current_phase_idx = (current_phase_idx + 1) % len(phases)
            if current_phase_idx == 0 and target_idx == phases[-1][0] : # If just finished last phase and it was going down to 0
                 pass # allow it to restart from phase 0 naturally
            target_idx, direction = phases[current_phase_idx]
        elif direction == -1 and next_scale_idx <= target_idx:
            next_scale_idx = target_idx
            current_phase_idx = (current_phase_idx + 1) % len(phases)
            target_idx, direction = phases[current_phase_idx]
        
        current_scale_idx = max(0, min(len(melody_range_scale) - 1, next_scale_idx))
        melodic_root_pitch = melody_range_scale[current_scale_idx]
        
        duration_choices = [0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.5]
        duration = random.choice(duration_choices)

        # --- Bass Line Note ---
        bass_note_pitch = melodic_root_pitch - 12 # One octave down
        if bass_note_pitch > 50: # If still higher than approx D3 (MIDI 50)
            bass_note_pitch -= 12 # Go down another octave
        bass_note_pitch = max(28, bass_note_pitch) # Ensure it's not below E1 (MIDI 28)
        
        mf.addNote(bass_track, bass_channel, bass_note_pitch, current_time, duration, bass_volume)

        # --- Melody/Chord ---
        play_triad = False
        current_note_chromatic_value = melodic_root_pitch % 12
        base_scale_degree_index = -1
        for i, base_note_midi in enumerate(bb_mixolydian_base_midi):
            if base_note_midi % 12 == current_note_chromatic_value:
                base_scale_degree_index = i
                break
        
        if base_scale_degree_index != -1:
            triad_info = triads_info_map.get(base_scale_degree_index)
            if triad_info and triad_info["type"] in ["major", "minor"] and random.random() < 0.25:
                play_triad = True
        
        if play_triad:
            for interval in triad_info["intervals"]:
                note_to_add = melodic_root_pitch + interval
                mf.addNote(melody_track, melody_channel, note_to_add, current_time, duration, melody_volume)
        else:
            mf.addNote(melody_track, melody_channel, melodic_root_pitch, current_time, duration, melody_volume)
            
        current_time += duration

    with open(filename, "wb") as output_file:
        mf.writeFile(output_file)
    print(f"MIDI file '{filename}' generated successfully with melody and bass line.")

# Generate the MIDI file
generate_mixolydian_with_bass_midi()
