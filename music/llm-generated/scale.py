import random
from midiutil import MIDIFile

def generate_mixolydian_midi(filename="bb_mixolydian_melody.mid"):
    # Scale and MIDI setup
    bb_mixolydian_base_midi = [58, 60, 62, 63, 65, 67, 68]  # Bb3, C4, D4, Eb4, F4, G4, Ab4
    scale_midi_abs = []
    for i in range(3): # Create 3 octaves of the scale starting from Bb3
        for note in bb_mixolydian_base_midi:
            scale_midi_abs.append(note + 12 * i)
    
    # We'll primarily use the first two octaves for melody range, Bb3 to Ab5
    # The scale_midi_abs now contains Bb3, C4,... Ab4, Bb4, C5,... Ab5, Bb5, C6,... Ab6
    # Let's cap usable range for melody notes to avoid going too high quickly
    # We'll use notes from index 0 (Bb3) up to index 13 (Ab5) for melody, plus Bb5 (index 14) as a peak
    melody_range_scale = scale_midi_abs[0:14+1] # Bb3 to Bb5 inclusive (15 notes)


    triads_info_map = {
        # scale_degree_index: {"name": "Chord Name", "type": "major/minor/diminished", "intervals": [root, third, fifth]}
        0: {"name": "Bb Maj", "type": "major", "intervals": [0, 4, 7]},    # Bb (I)
        1: {"name": "C min", "type": "minor", "intervals": [0, 3, 7]},    # C (ii)
        2: {"name": "D dim", "type": "diminished", "intervals": [0, 3, 6]},# D (iii) - will be skipped
        3: {"name": "Eb Maj", "type": "major", "intervals": [0, 4, 7]},   # Eb (IV)
        4: {"name": "F min", "type": "minor", "intervals": [0, 3, 7]},    # F (v)
        5: {"name": "G min", "type": "minor", "intervals": [0, 3, 7]},    # G (vi)
        6: {"name": "Ab Maj", "type": "major", "intervals": [0, 4, 7]}    # Ab (bVII)
    }

    # MIDI parameters
    track = 0
    channel = 0
    tempo = 100  # BPM
    volume = 100 # 0-127

    mf = MIDIFile(1)  # One track
    mf.addTempo(track, 0, tempo)
    mf.addProgramChange(track, channel, 0, 0) # Program 0: Acoustic Grand Piano

    current_time = 0.0
    current_scale_idx = 0 # Start at Bb3
    num_events = 120 # Total number of musical events (notes or chords)

    # Melodic phases: [target_scale_index, direction]
    phases = [
        (len(melody_range_scale) - 1, 1),  # Ascend to Bb5
        (0, -1),                           # Descend to Bb3
        (len(melody_range_scale) // 2, 1), # Ascend to Bb4 (middle)
        (0, -1)                            # Descend to Bb3
    ]
    current_phase_idx = 0
    target_idx, direction = phases[current_phase_idx]

    for _ in range(num_events):
        # Determine next note index with random variation
        rand_motion = random.random()
        step_size = 0
        if rand_motion < 0.75: # Normal step
            step_size = direction
        elif rand_motion < 0.90: # Jump a scale step
            step_size = 2 * direction
        else: # Repeat current note (effectively step_size = 0 for index change)
            step_size = 0

        next_scale_idx = current_scale_idx + step_size
        
        # Boundary checks and phase progression
        if direction == 1 and next_scale_idx >= target_idx: # Reached or passed ascending target
            next_scale_idx = target_idx
            current_phase_idx = (current_phase_idx + 1) % len(phases)
            target_idx, direction = phases[current_phase_idx]
        elif direction == -1 and next_scale_idx <= target_idx: # Reached or passed descending target
            next_scale_idx = target_idx
            current_phase_idx = (current_phase_idx + 1) % len(phases)
            target_idx, direction = phases[current_phase_idx]
        
        # Ensure next_scale_idx is within bounds of our chosen melodic range
        current_scale_idx = max(0, min(len(melody_range_scale) - 1, next_scale_idx))

        melody_note_pitch = melody_range_scale[current_scale_idx]
        
        # Determine duration
        duration_choices = [0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.5] # Weighted towards 1.0
        duration = random.choice(duration_choices)

        # Decide whether to play a single note or a triad
        play_triad = False
        scale_degree_index = (melody_range_scale[current_scale_idx] - bb_mixolydian_base_midi[0]) % 12
        # More robust way to get scale degree for triad lookup (0-6)
        # Find which of the base notes our current melody_note_pitch corresponds to (ignoring octave)
        # Example: if melody_note_pitch is 70 (Bb4), its base is 58 (Bb3). (70-58)%12 = 0. This is index 0 for triads.
        # if melody_note_pitch is 60 (C4), its base is 60. (60-58)%12 = 2, but C is the *second* note of Bb mixo.
        # So, we need the index within the 7 notes of the scale:
        
        # Find the root note in the base octave for the current melody_note_pitch
        current_note_chromatic_value = melody_note_pitch % 12
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
                # Add triad notes, ensuring they don't go excessively high or low
                # For simplicity, triads are played with root as the current melody note
                note_to_add = melody_note_pitch + interval
                mf.addNote(track, channel, note_to_add, current_time, duration, volume)
        else:
            mf.addNote(track, channel, melody_note_pitch, current_time, duration, volume)
            
        current_time += duration

    with open(filename, "wb") as output_file:
        mf.writeFile(output_file)
    print(f"MIDI file '{filename}' generated successfully.")

# Generate the MIDI file
generate_mixolydian_midi()
