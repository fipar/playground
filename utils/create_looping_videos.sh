#!/bin/bash

# Created by Claude Code
# Script to create looping videos from MOV files
# Usage: ./create_looping_videos.sh <directory>

# Check if directory argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <directory>"
    echo "Example: $0 /path/to/mov/files"
    exit 1
fi

DIR="$1"

# Check if directory exists
if [ ! -d "$DIR" ]; then
    echo "Error: Directory '$DIR' does not exist"
    exit 1
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed"
    echo "Install it with: brew install ffmpeg"
    exit 1
fi

# Number of times to loop the video
LOOP_COUNT=10

echo "Processing MOV files in: $DIR"
echo "Each video will loop $LOOP_COUNT times"
echo ""

# Counter for processed files
count=0

# Change to target directory to avoid path issues
cd "$DIR" || exit 1

# Process all .mov files (case-insensitive)
shopt -s nullglob nocaseglob
for input_file in *.mov; do
    # Skip if no files match
    [ -f "$input_file" ] || continue

    # Get filename without extension
    base="${input_file%.*}"

    echo "Processing: $input_file"
    echo "  -> Creating: ${base}_loop.mp4"

    # Create looping video using ffmpeg
    # - Use stream_loop to repeat the input multiple times
    # - Encode to H.264 with AAC audio for maximum compatibility
    # - Use settings optimized for mobile and WhatsApp
    if ffmpeg -hide_banner -loglevel warning -stream_loop $((LOOP_COUNT - 1)) -i "$input_file" \
        -c:v libx264 -preset medium -crf 23 \
        -pix_fmt yuv420p \
        -movflags +faststart \
        -y "${base}_loop.mp4" 2>&1; then
        echo "  ✓ Success"
        ((count++))
    else
        echo "  ✗ Failed"
    fi
    echo ""
done

echo "Done! Processed $count file(s)"
