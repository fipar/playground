# CLI to GUI Wrapper Design

## Overview

A Python-based GUI tool for macOS that automatically generates graphical interfaces for command-line scripts. The tool takes a single argument (path to a CLI script) and dynamically builds a GUI form based on the script's argument definitions.

## Goals

- Zero external dependencies (Tkinter only)
- Automatic argument discovery via AST parsing with fallback to help text parsing
- Intelligent widget selection based on argument types and context
- Safe handling of long-running processes and large outputs
- Multiple execution support without restarting the GUI

## Test Case

Primary test script: `~/src/playground/music/llm-generated/tuned-mosaic.py`
- Complex argparse definition with 20+ arguments
- Mix of required/optional arguments, choices, boolean flags, multi-value args
- File path arguments (`--reference`, `--sources`) that don't follow standard naming patterns
- Long-running execution with progress output (tqdm)

## Architecture

### Component Overview

The tool consists of four main components:

1. **ArgumentParser Discovery Module**
   - Primary: AST-based parsing of argparse definitions
   - Fallback: Help text parsing via `--help` execution
   - Output: Normalized argument specification

2. **GUI Generator Module**
   - Dynamic Tkinter form builder
   - Widget type selection based on argument metadata
   - Input validation and default value population

3. **Execution Controller**
   - Background thread management
   - Subprocess control with cancellation
   - Thread-safe output communication

4. **Output Display Widget**
   - Scrollable text output with rolling buffer
   - Dual output (GUI + terminal passthrough)
   - Status tracking and error highlighting

## Argument Parsing Strategy

### AST-Based Parsing (Primary Method)

Parse Python source code using AST to extract argparse definitions:

**Extracted Information:**
- Argument names (short and long forms: `-r`, `--reference`)
- Type specifications (`type=int`, `type=float`, `type=str`)
- Default values
- Choices lists
- Action types (`store_true`, `store_false`, `append`, etc.)
- `nargs` values (`+`, `*`, `?`, or numeric)
- Required flag
- Help text
- Metavar hints

**Implementation Approach:**
```python
# Parse script with ast.parse()
# Walk AST looking for:
# - ArgumentParser() instantiation
# - add_argument() method calls
# Extract literal values from AST nodes
```

### Widget Type Detection (Multi-Strategy)

Priority order for determining widget type:

1. **Explicit choices** → Dropdown menu (`ttk.Combobox`)
2. **Boolean actions** → Checkbox (`ttk.Checkbutton`)
3. **Path indicators** → File/Directory picker:
   - Help text patterns: "path to", "file", "directory", "output", "input"
   - Argument name patterns: "file", "path", "dir", "output", "input", "reference", "source"
   - Metavar hints: "FILE", "PATH", "DIR"
   - Type hints: `argparse.FileType` or path-related types
4. **Multi-value** (`nargs='+'` or `nargs='*'`) → List widget
5. **Numeric types** (`type=int`, `type=float`) → Number entry with validation
6. **Default** → Text entry

### Help Text Fallback Parser

When AST parsing fails or argparse isn't detected:

1. Execute `script --help` and capture output
2. Split into sections (positional/optional arguments)
3. Parse with regex patterns:
   - `-r, --reference PATH    Path to reference file`
   - Extract: flags, metavar, description
4. Infer types from metavars and descriptions
5. Extract defaults from help text patterns

## GUI Layout and Widgets

### Main Window Structure

Three-section vertical layout:

#### 1. Header Section (~50px, fixed)
- Script name/path label
- Optional description from script docstring

#### 2. Arguments Section (middle, scrollable)
- Scrollable canvas containing dynamic form
- 2-column grid layout: `[Label] [Widget]`
- Grouping: Required arguments first, then optional
- Each row includes:
  - Label (left-aligned)
  - Input widget (right-aligned, fills width)
  - Help icon ("?" button) with tooltip

#### 3. Execution Section (~300px, fixed)
- Control buttons row:
  - "Run Script" (green, primary)
  - "Cancel" (red, disabled until running)
  - "Reset Form" (gray, restores defaults)
- Output text area (monospace, scrollable, read-only)
- Status bar: execution state, elapsed time, line count

### Widget Implementations

| Argument Type | Widget | Implementation |
|---------------|--------|----------------|
| Text/String | Text Entry | `ttk.Entry` |
| Integer/Float | Number Entry | `ttk.Spinbox` with validation |
| Boolean Flag | Checkbox | `ttk.Checkbutton` |
| Choices | Dropdown | `ttk.Combobox` (read-only) |
| File Path | File Picker | `ttk.Entry` + "Browse" button → `filedialog.askopenfilename()` |
| Directory | Dir Picker | `ttk.Entry` + "Browse" button → `filedialog.askdirectory()` |
| Multi-value | List Widget | `tk.Listbox` + Add/Remove buttons + text entry |

### Form Validation

Pre-execution validation checks:

- Required arguments are filled
- Numeric fields contain valid numbers
- File paths exist (for input files)
- Parent directories exist (for output files)
- Display error dialog listing all validation failures

## Execution and Threading

### Threading Architecture

**Main Thread:**
- Handles all Tkinter events
- Updates UI components
- Polls output queue every 100ms

**Worker Thread:**
- Spawns subprocess
- Reads stdout/stderr
- Pushes output to queue
- Daemon thread (exits with main)

**Communication:**
- `queue.Queue` for thread-safe message passing
- Message types: output line, status update, completion

### Execution Flow

1. User clicks "Run Script"
2. Validate form inputs (main thread)
3. Build command line from form values
4. Update UI state:
   - Disable "Run" button
   - Enable "Cancel" button
   - Clear output area
   - Start timer
5. Spawn worker thread
6. Worker thread:
   - Create `subprocess.Popen()` with pipes
   - Read output line-by-line
   - Push to queue
   - Wait for completion
   - Push exit code
7. Main thread:
   - Poll queue via `after(100, check_queue)`
   - Update output widget
   - Update status bar
8. On completion:
   - Re-enable "Run"
   - Disable "Cancel"
   - Show final status

### Subprocess Configuration

```python
subprocess.Popen(
    ['python', script_path] + args,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,  # Merge stderr into stdout
    text=True,
    bufsize=1,  # Line buffered
    universal_newlines=True
)
```

### Cancellation Mechanism

1. "Cancel" button sets threading event flag
2. Worker thread checks flag in read loop
3. Call `process.terminate()` (SIGTERM)
4. Wait up to 5 seconds
5. Call `process.kill()` (SIGKILL) if still running
6. Clean up and exit worker thread
7. Update GUI: "Cancelled by user"

### Command Line Building

Argument conversion rules:

| Type | Conversion |
|------|-----------|
| Regular arg | `['--arg', value]` |
| Boolean True | `['--flag']` |
| Boolean False | Omit |
| Multi-value | `['--sources', 'file1', 'file2', 'file3']` |
| Positional | Append without prefix |

Handle shell escaping for:
- Paths with spaces
- Special characters
- Quote wrapping when needed

## Output Handling and Safety

### Rolling Buffer Management

Prevent memory issues with unlimited output:

- **Buffer limit:** 10,000 lines maximum
- **Pruning strategy:** Delete oldest 1,000 lines when limit reached
- **Indicator:** Show "[Output truncated - showing last 10,000 lines]" at top
- **No data loss:** All output still goes to terminal

### Text Widget Implementation

- `tk.Text` with `state='disabled'` (read-only)
- Temporarily enable for insertions
- Auto-scroll to bottom (unless user manually scrolled)
- Monospace font (Courier/Menlo on macOS)

**Syntax Highlighting:**
- Errors (contains "error", "failed"): red
- Warnings: orange
- Progress indicators: blue

### Dual Output Strategy

**1. GUI Output:**
- Display in text widget with formatting
- Subject to 10,000 line limit
- User can scroll, select, copy

**2. Terminal Passthrough:**
- Worker thread prints to `sys.stdout`
- No truncation
- Full log preservation
- Works when launched from terminal

### Performance Safeguards

- **Batch updates:** Queue up to 50 lines, insert together
- **Update throttling:** Max 10 updates/second
- **Line length limit:** Truncate lines over 1,000 chars
- **Memory monitoring:** Aggressive pruning if text widget exceeds 5MB

### Error Handling

- Catch subprocess errors (file not found, permissions, etc.)
- Display Python tracebacks in output area
- Highlight non-zero exit codes in red
- Handle script crashes gracefully
- Always re-enable controls

## Implementation Notes

### File Structure

```
script-ui/
├── script_gui.py          # Main executable
├── docs/
│   └── plans/
│       └── 2026-01-01-cli-gui-wrapper-design.md
└── README.md              # Usage documentation
```

### Entry Point

```bash
python script_gui.py /path/to/target/script.py
```

### Dependencies

- Python 3.7+ (for AST features)
- Tkinter (bundled with Python)
- No external packages required

### Platform Support

- Primary target: macOS
- Should work on Linux/Windows with native Tkinter theming
- Uses ttk widgets for native look and feel

## Future Enhancements (Not Implemented)

- Save/load argument presets to JSON
- Command history with quick recall
- Export command line to clipboard
- Diff view for comparing multiple runs
- Profile management for frequently-used argument sets
- Dark mode support
- Custom widget plugins

## Testing Strategy

### Manual Testing

1. Test with `tuned-mosaic.py`:
   - Verify all 20+ arguments detected
   - Test file picker for `--reference` and `--sources`
   - Verify multi-value handling for `--sources`
   - Test boolean flags and choices
   - Run full execution with progress output

2. Test edge cases:
   - Script with no arguments
   - Script without argparse (help text fallback)
   - Very long output (10,000+ lines)
   - Script that crashes
   - Cancellation during execution

3. Test validation:
   - Missing required arguments
   - Invalid numeric inputs
   - Non-existent file paths

### Success Criteria

- GUI launches within 1 second
- Correctly detects all argument types in test script
- Execution doesn't freeze GUI
- Output updates in real-time
- Cancellation works within 1 second
- No memory issues with long output
- Can execute script multiple times without restart
