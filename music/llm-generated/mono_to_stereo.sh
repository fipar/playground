#!/bin/bash
# Converts a mono audio file to a stereo file by duplicating the channel.
# Usage: ./mono_to_stereo.sh <input_file> <output_file>

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input_file> <output_file>"
    exit 1
fi

IN_FILE="$1"
OUT_FILE="$2"

# Use ffmpeg to convert to stereo by duplicating the mono channel
ffmpeg -i "$IN_FILE" -ac 2 "$OUT_FILE"

echo "Converted $IN_FILE to stereo and saved as $OUT_FILE"
