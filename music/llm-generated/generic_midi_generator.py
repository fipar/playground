import random
from midiutil import MIDIFile

# Attempt to import scales and modes; provide fallback or error if not found.
try:
    from musical_scales import SCALES_AND_MODES, get_diatonic_triads_major, get_diatonic_triads_natural_minor, get_diatonic_triads_mixolydian
except ImportError:
    print("Warning: musical_scales.py not found. Predefined scales will not be available.")
    SCALES_AND_MODES = {}
    def get_diatonic_triads_major(): return {}
    def get_diatonic_triads_natural_minor(): return {}
    def get_diatonic_triads_mixolydian(): return {}

class GenericMidiGenerator:
    def __init__(self,
                 base_scale_midi,
                 num_octaves=3,
                 melody_octave_range=2,
                 triads_info_map=None,
                 chord_probability=0.25,
                 prob_change_direction=0.1, # Probability to change the current melodic direction (up/down)
                 prob_step_relative=0.70, # Probability of a 1-note step in the current direction
                 prob_jump_relative=0.20, # Probability of a 2-note jump in the current direction
                                           # Remainder (1.0 - sum) is prob of 0-step (staying on scale index)
                 phrase_repetition_probability=0.1,
                 modulation_interval_events=50, # How often to consider modulating (in events)
                 modulation_probability=0.2, # Probability of modulating when interval is reached
                 modulation_options=None, # List of {'scale_info': scale_dict, 'triads_info_map': triad_dict}
                 swing_probability=0.0, # Probability for a note's timing to be shifted
                 swing_offset_denominator=0, # Max timing offset = 1/denominator of a beat (e.g., 8 for +/- 1/8th beat)
                 min_repeat_phrase_length=2,
                 max_repeat_phrase_length=5,
                 history_buffer_factor=3, # history size = max_repeat_phrase_length * factor
                 tempo=120,
                 program_number=0,  # 0: Acoustic Grand Piano
                 volume=100,
                 num_events=120,
                 duration_choices=[0.25, 0.5, 0.5, 1.0, 1.0, 1.5] # Rhythmic variety
                 ):
        self.base_scale_midi = base_scale_midi
        self.num_octaves = num_octaves
        self.melody_octave_range = melody_octave_range
        self.triads_info_map = triads_info_map
        # Disable chords if no triad map is provided
        self.chord_probability = chord_probability if self.triads_info_map else 0.0
        self.prob_change_direction = prob_change_direction
        # Renamed for clarity as they are relative to the *current* direction
        self.prob_step_relative = prob_step_relative
        self.prob_jump_relative = prob_jump_relative

        self.phrase_repetition_probability = phrase_repetition_probability
        self.min_repeat_phrase_length = max(1, min_repeat_phrase_length) # Ensure at least 1
        self.max_repeat_phrase_length = max(self.min_repeat_phrase_length, max_repeat_phrase_length)
        self.history_buffer_size = self.max_repeat_phrase_length * history_buffer_factor
        self.tempo = tempo
        self.program_number = program_number
        self.volume = volume
        self.num_events = num_events
        self.duration_choices = duration_choices
        self.modulation_interval_events = modulation_interval_events
        self.modulation_probability = modulation_probability
        self.modulation_options = modulation_options if modulation_options is not None else []
        self.swing_probability = swing_probability
        self.swing_offset_denominator = swing_offset_denominator

        if not self.base_scale_midi:
            raise ValueError("base_scale_midi cannot be empty.")

        self._build_scale()
        self._setup_melody_range()

    def _build_scale(self):
        self.scale_midi_abs = []
        for i in range(self.num_octaves):
            for note in self.base_scale_midi:
                self.scale_midi_abs.append(note + 12 * i)

    def _setup_melody_range(self):
        num_notes_in_base = len(self.base_scale_midi)
        notes_for_melody_span = num_notes_in_base * self.melody_octave_range
        # Ensure we have at least one note in the melody range
        end_index = min(len(self.scale_midi_abs), notes_for_melody_span + 1)
        if end_index == 0 and self.scale_midi_abs: # If num_octaves or melody_octave_range is 0
            end_index = min(len(self.scale_midi_abs), num_notes_in_base)

        self.melody_range_scale = self.scale_midi_abs[0:end_index]

        if not self.melody_range_scale:
            # Fallback if scale construction failed to produce a usable range
            print("Warning: Melody range scale is empty. Defaulting to a single note (60).")
            self.melody_range_scale = [60]


    def generate_midi(self, filename="generated_melody.mid"):
        mf = MIDIFile(1)  # One track
        track = 0
        channel = 0
        mf.addTempo(track, 0, self.tempo)
        mf.addProgramChange(track, channel, 0, self.program_number)

        current_time = 0.0
        current_scale_idx = 0

        melody_len = len(self.melody_range_scale)
        current_direction = random.choice([-1, 1]) # Start randomly up or down
        if melody_len <= 1: # Force direction to 0 or 1 if only one note
             current_direction = 1
             current_scale_idx = 0


        event_history = []  # Stores (list_of_pitches, duration) for phrase repetition
        events_generated = 0

        while events_generated < self.num_events:
            # --- Phrase Repetition ---
            if event_history and \
               random.random() < self.phrase_repetition_probability and \
               len(event_history) >= self.min_repeat_phrase_length:

                max_possible_len = min(self.max_repeat_phrase_length, len(event_history))
                
                if max_possible_len >= self.min_repeat_phrase_length:
                    phrase_len_to_repeat = random.randint(self.min_repeat_phrase_length, max_possible_len)
                    
                    # Ensure we don't exceed num_events
                    actual_phrase_len_to_repeat = min(phrase_len_to_repeat, self.num_events - events_generated)

                    if actual_phrase_len_to_repeat > 0:
                        phrase_to_repeat = event_history[-actual_phrase_len_to_repeat:]
                        # print(f"Time {current_time:.2f}: Repeating phrase of {len(phrase_to_repeat)} events.")
                        for event_data_idx, event_data in enumerate(phrase_to_repeat):
                            if events_generated >= self.num_events: break
                            pitches_to_play, event_duration = event_data
                            for pitch in pitches_to_play:
                                mf.addNote(track, channel, pitch, current_time, event_duration, self.volume)
                            current_time += event_duration
                            events_generated += 1
                        if events_generated >= self.num_events: break
                        continue # Skip new note generation for this iteration

            # --- New Note/Chord Generation ---

            # --- Melodic Direction Logic ---
            # Check if we hit a boundary, force direction change if so
            if melody_len > 1:
                if current_scale_idx == 0 and current_direction == -1:
                    current_direction = 1
                elif current_scale_idx == melody_len - 1 and current_direction == 1:
                    current_direction = -1
                # Otherwise, roll for a random direction change
                elif random.random() < self.prob_change_direction:
                     current_direction *= -1 # Flip direction

            # --- Melodic Step/Jump Logic (relative to current direction) ---
            rand_motion = random.random()
            step_size = 0
            if rand_motion < self.prob_step_relative:
                step_size = 1 * current_direction
            elif rand_motion < self.prob_step_relative + self.prob_jump_relative:
                step_size = 2 * current_direction
            # Else: step_size = 0 (stay on current scale index for the new note)

            next_scale_idx = current_scale_idx + step_size

            # Clamp next_scale_idx to stay within bounds
            current_scale_idx = max(0, min(melody_len - 1, next_scale_idx))

            # --- Modulation Logic ---
            events_since_modulation = events_generated # Use events_generated as counter
            if self.modulation_options and \
               events_since_modulation > 0 and \
               events_since_modulation % self.modulation_interval_events == 0 and \
               random.random() < self.modulation_probability:

                print(f"Time {current_time:.2f}: Attempting modulation...")
                chosen_mod_option = random.choice(self.modulation_options)
                new_scale_info = chosen_mod_option["scale_info"]
                new_triads_map = chosen_mod_option.get("triads_info_map", None) # Triads map is optional

                old_melodic_root_pitch = self.melody_range_scale[current_scale_idx]

                self.base_scale_midi = new_scale_info["notes"]
                self._build_scale() # Rebuild the full scale
                self._setup_melody_range() # Re-establish the melody range
                self.triads_info_map = new_triads_map # Update triad map
                melody_len = len(self.melody_range_scale) # Update melody length

                # Find the closest note in the new melody range scale to the old pitch
                min_diff = float('inf')
                closest_idx = 0
                # Handle case where new melody range is empty (shouldn't happen with fallback)
                if melody_len > 0:
                    for i, new_pitch in enumerate(self.melody_range_scale):
                        diff = abs(new_pitch - old_melodic_root_pitch)
                        if diff < min_diff:
                            min_diff = diff
                            closest_idx = i
                    current_scale_idx = closest_idx # Set the index to the closest note in the new scale
                    print(f"Modulated to {new_scale_info['root_name']} {new_scale_info['type']}. New melody range length: {melody_len}. Starting at index {current_scale_idx}.")
                else:
                     print("Warning: New melody range is empty after modulation. Cannot continue.")
                     break # Exit loop if modulation resulted in unusable scale

            melodic_root_pitch = self.melody_range_scale[current_scale_idx]
            duration = random.choice(self.duration_choices)

            # --- Swing/Humanization Logic ---
            # The `current_time` is the note's ideal start time on the grid.
            # `note_start_time_for_midi` will be the actual time written to the MIDI file.
            note_start_time_for_midi = current_time

            if self.swing_offset_denominator and self.swing_offset_denominator > 0 and \
               self.swing_probability > 0 and random.random() < self.swing_probability:
                
                max_abs_offset_beats = 1.0 / self.swing_offset_denominator
                timing_offset = random.uniform(-max_abs_offset_beats, max_abs_offset_beats)
                
                # Apply offset, ensuring the note doesn't start before time 0.0
                note_start_time_for_midi = max(0.0, current_time + timing_offset)

            pitches_for_this_event = []
            play_triad = False
            if self.triads_info_map and self.chord_probability > 0 and \
               random.random() < self.chord_probability:
                
                current_note_chromatic_value = melodic_root_pitch % 12
                base_scale_degree_index = -1
                for i, base_note_midi in enumerate(self.base_scale_midi):
                    if base_note_midi % 12 == current_note_chromatic_value:
                        base_scale_degree_index = i
                        break
                
                if base_scale_degree_index != -1:
                    triad_info = self.triads_info_map.get(base_scale_degree_index)
                    if triad_info and triad_info["type"] in ["major", "minor"]: # Only major/minor for now
                        play_triad = True
            
            if play_triad:
                for interval in triad_info["intervals"]:
                    note_to_add = melodic_root_pitch + interval
                    pitches_for_this_event.append(note_to_add)
                    mf.addNote(track, channel, note_to_add, note_start_time_for_midi, duration, self.volume)
            else:
                pitches_for_this_event.append(melodic_root_pitch)
                mf.addNote(track, channel, melodic_root_pitch, note_start_time_for_midi, duration, self.volume)
            
            event_history.append((pitches_for_this_event, duration))
            if len(event_history) > self.history_buffer_size:
                event_history.pop(0)

            # IMPORTANT: Advance the main `current_time` by the ideal duration,
            # maintaining the metronomic grid for subsequent calculations.
            # The `note_start_time_for_midi` only affects where this specific note is placed.
            current_time += duration
            events_generated += 1

        with open(filename, "wb") as output_file:
            mf.writeFile(output_file)
        print(f"MIDI file '{filename}' generated successfully with {events_generated} events.")


if __name__ == "__main__":
    # --- Default/Base Configuration ---
    # These can be overridden by specific configurations below
    base_generator_config = {
        "num_octaves": 3,
        "melody_octave_range": 2, # Use ~2 octaves for melody range from base
        "chord_probability": 0.3, # 30% chance of a chord
        "prob_step_relative": 0.65,  # Updated key name
        "prob_jump_relative": 0.25, # Updated key name (0.65+0.25 = 0.90, so 10% chance of 0-step)
        "prob_change_direction": 0.1, # 10% chance to change direction at each step
        "phrase_repetition_probability": 0.15, # 15% chance to repeat a phrase
        "swing_probability": 0.0, # Default to no swing probability
        "swing_offset_denominator": 0, # Default to no swing offset (e.g., 8 for +/- 1/8 beat)
        # Modulation parameters added below in specific examples
        "min_repeat_phrase_length": 2,
        "max_repeat_phrase_length": 6,
        "history_buffer_factor": 3,
        "tempo": 100,
        "program_number": 0, # Acoustic Grand Piano
        "volume": 100,
        "num_events": 150,
        "duration_choices": [0.25, 0.5, 0.5, 0.75, 1.0, 1.0, 1.5]
    }

    # # --- Configuration Example 1: C Major ---
    # if "C_MAJOR" in SCALES_AND_MODES:
    #     c_major_scale_info = SCALES_AND_MODES["C_MAJOR"]

    #     # Define possible modulation targets for C Major example
    #     c_major_modulation_options = [
    #         {"scale_info": SCALES_AND_MODES.get("G_MAJOR"), "triads_info_map": get_diatonic_triads_major()}, # Modulate to Dominant
    #     ]
        
    #     config_c_major = base_generator_config.copy()
    #     config_c_major.update({
    #         "base_scale_midi": c_major_scale_info["notes"],
    #         "triads_info_map": get_diatonic_triads_major(),
    #         "tempo": 90,
    #         "num_events": 100,
    #         "phrase_repetition_probability": 0.05,
    #         "program_number": 56, # Trumpet
    #         "prob_change_direction": 0.2, # More frequent direction changes
    #         "modulation_interval_events": 40, # Consider modulating every 40 events
    #         "modulation_probability": 0.3, # 30% chance to modulate when interval is reached
    #         "swing_probability": 0.6,      # 60% chance for a note to be swung
    #         "swing_offset_denominator": 16, # Max offset +/- 1/16th of a beat
    #         "filename": "generated_c_major.mid"
    #     })

    #     output_filename_c_major = config_c_major.pop("filename") # Extract filename
    #     midi_gen_c_major = GenericMidiGenerator(**config_c_major) # Pass config without filename
    #     midi_gen_c_major.generate_midi(output_filename_c_major)   # Use extracted filename

    # else:
    #     print("C_MAJOR scale not found in SCALES_AND_MODES. Skipping C Major example.")

    # # --- Configuration Example 2: G Mixolydian ---
    # if "G_MIXOLYDIAN" in SCALES_AND_MODES:
    #     g_mixolydian_info = SCALES_AND_MODES["G_MIXOLYDIAN"]

    #     # Define possible modulation targets for G Mixolydian example
    #     g_mixolydian_modulation_options = [
    #         {"scale_info": SCALES_AND_MODES.get("C_MAJOR"), "triads_info_map": get_diatonic_triads_major()}, # Modulate to IV (C Major)
    #         {"scale_info": SCALES_AND_MODES.get("D_DORIAN"), "triads_info_map": None}, # Modulate to ii (D Dorian), no chords
    #     ]

    #     config_g_mixolydian = base_generator_config.copy()
    #     config_g_mixolydian.update({
    #         "base_scale_midi": g_mixolydian_info["notes"],
    #         "triads_info_map": get_diatonic_triads_mixolydian(), # Using specific mixolydian triads
    #         "chord_probability": 0.35,
    #         "tempo": 110,
    #         "program_number": 26, # Steel Guitar
    #         "num_events": 160,
    #         "prob_change_direction": 0.15,
    #         "modulation_interval_events": 60,
    #         "modulation_probability": 0.4,
    #         "swing_probability": 0.75,
    #         "swing_offset_denominator": 12, # Max offset +/- 1/12th of a beat
    #         "filename": "generated_g_mixolydian.mid"
    #     })

    #     output_filename_g_mixolydian = config_g_mixolydian.pop("filename") # Extract filename
    #     midi_gen_g_mixolydian = GenericMidiGenerator(**config_g_mixolydian) # Pass config without filename
    #     midi_gen_g_mixolydian.generate_midi(output_filename_g_mixolydian)   # Use extracted filename

    # else:
    #     print("G_MIXOLYDIAN scale not found. Skipping G Mixolydian example.")

    # --- Configuration Example 3: D Natural Minor, no chords ---
    if "D_NATURAL_MINOR" in SCALES_AND_MODES:
        d_minor_scale_info = SCALES_AND_MODES["D_NATURAL_MINOR"]

        # Define possible modulation targets for D Natural Minor example
        d_minor_modulation_options = [
             {"scale_info": SCALES_AND_MODES.get("F_MAJOR"), "triads_info_map": get_diatonic_triads_major()}, # Modulate to relative major (F Major)
             {"scale_info": SCALES_AND_MODES.get("A_NATURAL_MINOR"), "triads_info_map": get_diatonic_triads_natural_minor()}, # Modulate to v (A Minor)
        ]

        config_d_minor = base_generator_config.copy()
        config_d_minor.update({
        "base_scale_midi": d_minor_scale_info["notes"],
        "chord_probability": 0.4,
        "triads_info_map": get_diatonic_triads_natural_minor(), # Provide map, but low probability
        "tempo": 120,
        "prob_change_direction": 0.3, # More frequent direction changes
        "program_number": 42, # Cello
        "modulation_options": d_minor_modulation_options, # Add modulation options here
        "swing_probability": 0.1,      # 50% chance for a note to be swung
        "swing_offset_denominator": 16, # Max offset +/- 1/24th of a beat (subtle)
        "num_events": 140,
        "filename": "generated_d_natural_minor.mid"
        })

        output_filename_d_minor = config_d_minor.pop("filename") # Extract filename
        midi_gen_d_minor = GenericMidiGenerator(**config_d_minor) # Pass config without filename
        # Add modulation options *after* creating the generator instance,
        midi_gen_d_minor.generate_midi(output_filename_d_minor)   # Use extracted filename

    else:
        print("D_NATURAL_MINOR scale not found. Skipping D Natural Minor example.")

    print("Done generating MIDI files.")