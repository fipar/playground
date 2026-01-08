# Quick Start Guide

## Prerequisites (macOS ONLY)

**System Python's Tk is broken on macOS.** You must use Homebrew Python:

```bash
# Install Homebrew Python with Tk (one-time setup)
brew install python-tk@3.12

# Verify it works
/opt/homebrew/bin/python3.12 -c "import tkinter; print('✓ Tkinter OK')"
```

## Testing the GUI Wrapper

### 1. Test with the example script (recommended):

```bash
# Easy way - use the convenience script
./run-gui.sh example.py

# Or run directly with Homebrew Python
/opt/homebrew/bin/python3.12 script-ui.py example.py
```

You should see a window with:
- **Top section**: 14 input fields for different argument types
  - Required fields marked with `*` (Input File, Output File)
  - File browsers with "Browse..." buttons
  - Checkboxes for boolean options
  - Dropdowns for format and log-level
  - Number fields for count and threshold
- **Bottom section**: Terminal-style output area with dark background
- **Green "▶ Run Script" button** to execute

### 2. Try it with the complex audio script:

```bash
./run-gui.sh ../music/llm-generated/tuned-mosaic.py
```

This will show 22 arguments including:
- Multiple file selection for `--sources`
- Dropdown menus for `--window` type
- Various tuning checkboxes
- Numeric parameters

### 3. What to test:

1. **Click Browse buttons** - File/save dialogs should open
2. **Click checkboxes** - Should toggle on/off
3. **Use dropdowns** - Should show available choices
4. **Try to run without required fields** - Should show error dialog
5. **Fill in required fields and click Run** - Output should appear in terminal area

## Expected Behavior

### Working GUI Features:
- ✅ Window appears with all widgets visible
- ✅ Scrollbar works for long argument lists
- ✅ File dialogs open when clicking Browse
- ✅ Validation works for required fields
- ✅ Output displays in terminal area

### Using System Python (NOT RECOMMENDED):
System Python's Tk on macOS is completely broken - only buttons will be visible, no labels or text fields. **Always use Homebrew Python.**

## Troubleshooting

### Black window or nothing shows:
The latest version uses standard tk widgets and PanedWindow layout for maximum compatibility. If you still see issues:

1. Make sure you're on the latest commit:
   ```bash
   git log --oneline -1
   # Should show: "Fix listbox widgets to use tk instead of ttk"
   ```

2. Try running the example script first (simpler UI)

3. Check for Python/Tk errors:
   ```bash
   python3 script-ui.py example.py 2>&1 | grep -i error
   ```

### For best results:
Install Python via Homebrew for modern Tk:
```bash
brew install python-tk@3.12
```

## Example Run

Here's what happens when you run with example.py:

1. Fill in Input File: `/tmp/input.txt`
2. Fill in Output File: `/tmp/output.txt`
3. Select format: `json`
4. Check "Verbose"
5. Set count: `5`
6. Click "▶ Run Script"

Output should show:
```
Running: /usr/bin/python3 example.py --input-file /tmp/input.txt --output-file /tmp/output.txt ...

============================================================
Example Script - Arguments Received
============================================================
...
```
