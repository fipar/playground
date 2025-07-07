#!/bin/bash

# Check if an input file is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <input_audio_file>"
  exit 1
fi

INPUT_FILE="$1"
ORC_FILE="/Users/fernandoipar/Documents/audio-sources/up-next/binaural_random.orc"
SCO_TEMPLATE="/Users/fernandoipar/Documents/audio-sources/up-next/binaural_random.sco.template"
TEMP_SCO_FILE="/Users/fernandoipar/Documents/audio-sources/up-next/binaural_random_temp.sco"
OUTPUT_FILE="/Users/fernandoipar/Documents/audio-sources/up-next/output.wav"

# Get the duration of the input audio file using sox
DURATION=$(sox "$INPUT_FILE" -n stat 2>&1 | grep Length | awk '{print $3}' | cut -d'.' -f1)

# Add 1 to the duration to ensure full processing and round up
DURATION=$((DURATION + 1))

# Generate the temporary .sco file from the template
sed "s|_DURATION_|$DURATION|g; s|_INPUT_FILE_|$INPUT_FILE|g" "$SCO_TEMPLATE" > "$TEMP_SCO_FILE"

echo "Processing $INPUT_FILE (Duration: ${DURATION}s) with Csound..."

# Run Csound
csound -o "$OUTPUT_FILE" "$ORC_FILE" "$TEMP_SCO_FILE"

# Clean up the temporary .sco file
rm "$TEMP_SCO_FILE"

echo "Processing complete. Output saved to $OUTPUT_FILE"
