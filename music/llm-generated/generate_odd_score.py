#!/usr/bin/env python3
import random

# Configuration
BPM = 90
MEASURE = 16  # Using 16th notes as the base unit

# Four notes from C# Mixolydian scale
notes = ['C#3', 'F#3', 'G#3', 'B3']

# Each note repeats at different intervals (in 16th notes)
intervals = [14, 15, 21, 25]

# Calculate LCM to get one full cycle (when all patterns align again)
# LCM(14, 15, 21, 25) = 1050 sixteenth notes
total_positions = 1050

# Generate note events
events = []

for note, interval in zip(notes, intervals):
    position = 1  # Start at position 1 (1-indexed)
    while position <= total_positions:
        # Random duration from 1 (1/16) to 16 (1 whole note)
        duration = random.randint(1, 16)

        # Random velocity offset (keeping within MIDI range 0-127 with base 100)
        velocity_offset = random.randint(-30, 27)

        events.append((position, note, duration, velocity_offset))
        position += interval

# Sort events by position
events.sort()

# Write to file
with open('odd.score', 'w') as f:
    f.write(f'measure: {MEASURE}\n')
    f.write(f'tempo: {BPM}\n')
    f.write('instrument: piano\n')
    f.write('\n')

    for position, note, duration, velocity_offset in events:
        f.write(f'{position} {note} {duration} {velocity_offset}\n')

print(f"Generated odd.score with {len(events)} notes")
print(f"Total duration: {total_positions} sixteenth notes")
print(f"Note intervals: {dict(zip(notes, intervals))}")
