# Script-UI: GUI Wrapper Generator for Python CLI Scripts

Automatically generate graphical user interfaces (GUIs) for Python command-line scripts that use `argparse`.

## Overview

Script-UI analyzes any Python script that uses `argparse` and generates a user-friendly GUI wrapper with appropriate widgets for each argument type. No modifications to the original script are needed!

## Features

- **Automatic Analysis**: Parses Python scripts using AST to extract all argparse arguments
- **Intelligent Type Detection**:
  - Files and directories get browse buttons with file/directory pickers
  - Boolean flags become checkboxes
  - Arguments with choices become dropdown menus
  - Numbers (int/float) get text entry with validation
  - Multiple file selection with listbox interface
- **Smart Detection**:
  - Automatically detects file arguments by name (file, path, input, output, reference, source)
  - Automatically detects directory arguments by name (dir, directory, folder)
  - Respects `dest` parameter for renamed arguments
  - Handles both short (`-r`) and long (`--reference`) argument forms
- **Validation**: Checks required fields before execution and shows helpful error messages
- **Real-time Output**: Displays script output as it runs in a scrollable text area
- **Cross-platform**: Works on macOS, Linux, and Windows

## Installation

No installation needed! Just requires Python 3 with tkinter (usually included by default).

```bash
# Clone or download script-ui.py
chmod +x script-ui.py
```

## Usage

### Basic Usage

```bash
python script-ui.py <path_to_script.py>
```

### Example

Using the included test case:

```bash
python script-ui.py ../music/llm-generated/tuned-mosaic.py
```

This will:
1. Analyze `tuned-mosaic.py` and find all 22 argparse arguments
2. Generate a GUI with appropriate widgets:
   - **File browsers** for `--reference`, `--output`
   - **Multiple file selector** for `--sources`
   - **Dropdowns** for `--window` and `--mfcc-distance-metric` (with predefined choices)
   - **Checkboxes** for `--enable-pitch-tuning`, `--enable-volume-tuning`, etc.
   - **Number fields** for `--chunk-size-min`, `--overlap`, `--sr`, etc.
3. Mark required fields with asterisks (*)
4. Provide help text for each argument
5. Execute the script when you click "Run Script"
6. Show output in real-time

## How It Works

### 1. Script Analysis

Script-UI uses Python's `ast` module to parse the target script and find all `parser.add_argument()` calls. It extracts:

- Argument names (both short and long forms)
- Types (`str`, `int`, `float`, `bool`)
- Default values
- Required vs optional
- Help text
- Choices (for dropdown menus)
- Number of arguments (`nargs`)
- Action type (`store_true`, `store_false`, etc.)

### 2. Widget Selection

Based on the extracted information, Script-UI chooses the appropriate widget:

| Argument Type | Widget | Example |
|--------------|--------|---------|
| `action='store_true/false'` | Checkbox | `--enable-pitch-tuning` |
| `choices=[...]` | Dropdown (Combobox) | `--window` with choices |
| File path (single) | Text entry + Browse button | `--reference` |
| File path (multiple) | Listbox + Add/Remove buttons | `--sources` |
| Directory path | Text entry + Browse button | `--output-dir` |
| Number (`int`/`float`) | Text entry | `--chunk-size-min` |
| String | Text entry | Regular text arguments |

### 3. File/Directory Detection

Arguments are treated as file paths if their name contains:
- `file`, `path`, `input`, `output`, `reference`, `source`, `sources`

Arguments are treated as directory paths if their name contains:
- `dir`, `directory`, `folder`

### 4. Execution

When you click "Run Script":
1. Validates all required fields are filled
2. Builds the command line with all selected arguments
3. Executes the original script in a subprocess
4. Streams output to the GUI in real-time
5. Shows completion status

## Supported Argument Types

Script-UI handles all common argparse patterns:

```python
# Required arguments
parser.add_argument('-r', '--reference', required=True)

# Optional with defaults
parser.add_argument('--chunk-size', type=float, default=0.1)

# Boolean flags
parser.add_argument('--enable-tuning', action='store_true')

# Choices (dropdown)
parser.add_argument('--window', choices=['hann', 'hamming', 'blackman'])

# Multiple values
parser.add_argument('--sources', nargs='+', help='One or more files')

# Custom dest
parser.add_argument('--no-crossfade', dest='crossfade', action='store_false')
```

## Examples

### Example 1: Audio Processing Script

```bash
python script-ui.py tuned-mosaic.py
```

Generates GUI for audio mosaicing with:
- File pickers for audio files
- Sliders for parameters (chunk size, overlap)
- Checkboxes for tuning options
- Dropdown for window functions

### Example 2: Any argparse-based script

```python
# your_script.py
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', required=True, help='Input file')
parser.add_argument('--output', required=True, help='Output file')
parser.add_argument('--verbose', action='store_true', help='Verbose mode')
parser.add_argument('--quality', type=int, default=80, help='Quality (0-100)')
args = parser.parse_args()
```

```bash
python script-ui.py your_script.py
```

Gets a GUI automatically!

## Limitations

- Only works with scripts that use `argparse` (not `click`, `getopt`, etc.)
- Some complex argparse features may not be fully supported
- AST parsing requires valid Python syntax
- Subparsers and mutually exclusive groups are not yet supported

## Architecture

```
script-ui.py
│
├── ArgumentInfo          # Data class for argument metadata
├── ScriptAnalyzer        # AST-based script parser
│   ├── analyze()         # Main analysis entry point
│   ├── _visit_ast()      # AST traversal
│   └── _extract_argument_info()  # Parse add_argument() calls
│
└── GUIGenerator          # Tkinter GUI builder
    ├── create_gui()      # Main GUI construction
    ├── _create_argument_widget()  # Widget factory
    ├── _run_script()     # Execution handler
    └── _execute_command()  # Subprocess runner
```

## Development

### Running Tests

```bash
# Test with the included example
python script-ui.py ../music/llm-generated/tuned-mosaic.py
```

### Adding New Widget Types

To add support for new argument patterns, modify `GUIGenerator._create_argument_widget()`:

```python
elif arg.your_new_pattern():
    # Create your custom widget
    var = tk.StringVar()
    widget = YourCustomWidget(frame, textvariable=var)
    self.values[arg.name] = var
```

## Contributing

Contributions welcome! Areas for improvement:

- Support for more argparse features (subparsers, groups, etc.)
- Better validation for numeric inputs
- Save/load argument presets
- GUI themes and styling
- Support for other CLI frameworks (click, etc.)

## License

This tool is provided as-is for educational and practical use.

## Credits

Created to provide an easy way to add GUIs to existing command-line tools without modifying the original scripts.

Tested with `tuned-mosaic.py`, a complex audio processing script with 22+ arguments.
