def generate_scale(root_midi, intervals):
    """Generates a scale from a root MIDI note and a list of intervals."""
    scale = [root_midi]
    current_note = root_midi
    for interval in intervals[:-1]:  # Last interval brings back to octave, not needed for 7-note scale
        current_note += interval
        scale.append(current_note % 128) # Ensure MIDI note is within valid range
    return scale

# Interval patterns (W=2, H=1 semitone)
MAJOR_INTERVALS = [2, 2, 1, 2, 2, 2, 1]        # Ionian
NATURAL_MINOR_INTERVALS = [2, 1, 2, 2, 1, 2, 2] # Aeolian
DORIAN_INTERVALS = [2, 1, 2, 2, 2, 1, 2]
PHRYGIAN_INTERVALS = [1, 2, 2, 2, 1, 2, 2]
LYDIAN_INTERVALS = [2, 2, 2, 1, 2, 2, 1]
MIXOLYDIAN_INTERVALS = [2, 2, 1, 2, 2, 1, 2]
LOCRIAN_INTERVALS = [1, 2, 2, 1, 2, 2, 2]

# For harmonic and melodic minor, if needed later
# HARMONIC_MINOR_INTERVALS = [2, 1, 2, 2, 1, 3, 1]
# MELODIC_MINOR_ASC_INTERVALS = [2, 1, 2, 2, 2, 2, 1]

NOTE_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

SCALES_AND_MODES = {}

# Generate Major Scales (starting root MIDI notes from C4=60 to B4=71)
for i, note_name in enumerate(NOTE_NAMES):
    root_midi = 60 + i
    SCALES_AND_MODES[f"{note_name}_MAJOR"] = {
        "notes": generate_scale(root_midi, MAJOR_INTERVALS),
        "type": "major",
        "root_midi_note": root_midi,
        "root_name": note_name
    }

# Generate Natural Minor Scales
for i, note_name in enumerate(NOTE_NAMES):
    root_midi = 60 + i # C minor starts on C4, A minor on A4 etc.
    # To have A minor start on A3 (57) for a more traditional layout relative to C major:
    # root_midi_for_A_minor_example = 57 + i (if 'A' is the first in a reordered NOTE_NAMES for minor)
    # For simplicity, we'll keep roots in the 60-71 range. A natural minor will be A4 based.
    # If you want A minor to be [57, 59, 60, 62, 64, 65, 67], you'd set root_midi for "A_NATURAL_MINOR" to 57.
    # Here, A_NATURAL_MINOR will start on MIDI 69 (A4).
    SCALES_AND_MODES[f"{note_name}_NATURAL_MINOR"] = {
        "notes": generate_scale(root_midi, NATURAL_MINOR_INTERVALS),
        "type": "natural_minor",
        "root_midi_note": root_midi,
        "root_name": note_name
    }

# Modes of C Major (C Ionian is C_MAJOR)
# D Dorian (Root D4 = 62)
SCALES_AND_MODES["D_DORIAN"] = {
    "notes": generate_scale(62, DORIAN_INTERVALS),
    "type": "dorian", "root_midi_note": 62, "root_name": "D"
}
# E Phrygian (Root E4 = 64)
SCALES_AND_MODES["E_PHRYGIAN"] = {
    "notes": generate_scale(64, PHRYGIAN_INTERVALS),
    "type": "phrygian", "root_midi_note": 64, "root_name": "E"
}
# F Lydian (Root F4 = 65)
SCALES_AND_MODES["F_LYDIAN"] = {
    "notes": generate_scale(65, LYDIAN_INTERVALS),
    "type": "lydian", "root_midi_note": 65, "root_name": "F"
}
# G Mixolydian (Root G4 = 67)
SCALES_AND_MODES["G_MIXOLYDIAN"] = {
    "notes": generate_scale(67, MIXOLYDIAN_INTERVALS),
    "type": "mixolydian", "root_midi_note": 67, "root_name": "G"
}
# A Aeolian (Root A4 = 69) - same as A_NATURAL_MINOR
SCALES_AND_MODES["A_AEOLIAN"] = SCALES_AND_MODES["A_NATURAL_MINOR"]
SCALES_AND_MODES["A_AEOLIAN"]["type"] = "aeolian" # Ensure type is specific if needed

# B Locrian (Root B4 = 71)
SCALES_AND_MODES["B_LOCRIAN"] = {
    "notes": generate_scale(71, LOCRIAN_INTERVALS),
    "type": "locrian", "root_midi_note": 71, "root_name": "B"
}

# Some modes starting on C (C4 = 60)
SCALES_AND_MODES["C_DORIAN"] = {
    "notes": generate_scale(60, DORIAN_INTERVALS),
    "type": "dorian", "root_midi_note": 60, "root_name": "C"
}
SCALES_AND_MODES["C_LYDIAN"] = {
    "notes": generate_scale(60, LYDIAN_INTERVALS),
    "type": "lydian", "root_midi_note": 60, "root_name": "C"
}
SCALES_AND_MODES["C_MIXOLYDIAN"] = {
    "notes": generate_scale(60, MIXOLYDIAN_INTERVALS),
    "type": "mixolydian", "root_midi_note": 60, "root_name": "C"
}

# --- Diatonic Triad Generation Helpers ---
# These return maps of scale_degree_index -> triad_info
# The generator currently only uses "major" and "minor" triad types.

def get_diatonic_triads_major():
    """Returns a dictionary of diatonic triads for a major scale."""
    return {
        0: {"name": "I Maj", "type": "major", "intervals": [0, 4, 7]},
        1: {"name": "ii min", "type": "minor", "intervals": [0, 3, 7]},
        2: {"name": "iii min", "type": "minor", "intervals": [0, 3, 7]},
        3: {"name": "IV Maj", "type": "major", "intervals": [0, 4, 7]},
        4: {"name": "V Maj", "type": "major", "intervals": [0, 4, 7]},
        5: {"name": "vi min", "type": "minor", "intervals": [0, 3, 7]},
        # 6: {"name": "vii dim", "type": "diminished", "intervals": [0, 3, 6]} # Diminished
    }

def get_diatonic_triads_natural_minor():
    """Returns a dictionary of diatonic triads for a natural minor scale."""
    return {
        0: {"name": "i min", "type": "minor", "intervals": [0, 3, 7]},
        # 1: {"name": "ii dim", "type": "diminished", "intervals": [0, 3, 6]} # Diminished
        2: {"name": "III Maj", "type": "major", "intervals": [0, 4, 7]},
        3: {"name": "iv min", "type": "minor", "intervals": [0, 3, 7]},
        4: {"name": "v min", "type": "minor", "intervals": [0, 3, 7]}, # Often altered to V Maj
        5: {"name": "VI Maj", "type": "major", "intervals": [0, 4, 7]},
        6: {"name": "VII Maj", "type": "major", "intervals": [0, 4, 7]},
    }

def get_diatonic_triads_mixolydian():
    """Returns a dictionary of diatonic triads for a mixolydian scale."""
    return {
        0: {"name": "I Maj", "type": "major", "intervals": [0, 4, 7]},
        1: {"name": "ii min", "type": "minor", "intervals": [0, 3, 7]},
        # 2: {"name": "iii dim", "type": "diminished", "intervals": [0, 3, 6]},
        3: {"name": "IV Maj", "type": "major", "intervals": [0, 4, 7]},
        4: {"name": "v min", "type": "minor", "intervals": [0, 3, 7]},
        5: {"name": "vi min", "type": "minor", "intervals": [0, 3, 7]}, # Often vi dim in some contexts
        6: {"name": "bVII Maj", "type": "major", "intervals": [0, 4, 7]},
    }

# Add more triad helpers for other modes (Dorian, Lydian, etc.) if desired,
# keeping in mind the generator currently only plays "major" or "minor" types.

# Example: print(SCALES_AND_MODES["C_MAJOR"])
# Example: print(SCALES_AND_MODES["A_NATURAL_MINOR"])
# Example: print(get_diatonic_triads_major())
