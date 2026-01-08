#!/bin/bash
# Convenience script to run script-ui with Homebrew Python (which has working Tk)

# Find Homebrew Python 3.12
PYTHON=/opt/homebrew/bin/python3.12

if [ ! -f "$PYTHON" ]; then
    echo "Error: Homebrew Python 3.12 not found!"
    echo "Please install it with: brew install python-tk@3.12"
    exit 1
fi

# Check if tkinter is available
$PYTHON -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: Tkinter not available!"
    echo "Please install it with: brew install python-tk@3.12"
    exit 1
fi

# Run script-ui with the provided argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <python_script.py>"
    echo ""
    echo "Examples:"
    echo "  $0 example.py"
    echo "  $0 ../music/llm-generated/tuned-mosaic.py"
    exit 1
fi

echo "Launching GUI for: $1"
$PYTHON script-ui.py "$1"
