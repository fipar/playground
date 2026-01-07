#!/usr/bin/env python3
"""
Script-UI: Generate GUI wrappers for command-line Python scripts

This tool analyzes a Python script that uses argparse and generates a GUI wrapper
that provides an intuitive interface for all command-line arguments.

Features:
- Automatically detects argument types (files, strings, numbers, booleans)
- Provides file/directory selector dialogs for file-based arguments
- Generates appropriate widgets (text entry, checkboxes, dropdowns)
- Executes the wrapped script and displays output
- Intelligently handles required vs optional arguments

Usage:
    python script-ui.py <target_script.py>

Example:
    python script-ui.py ../music/llm-generated/tuned-mosaic.py
"""

import sys
import ast
import re
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import threading
from pathlib import Path


class ArgumentInfo:
    """Stores information about a command-line argument"""
    def __init__(self, name, arg_type='str', required=False, default=None,
                 help_text='', choices=None, nargs=None, action=None):
        self.name = name
        self.arg_type = arg_type  # 'str', 'int', 'float', 'bool', 'file', 'dir'
        self.required = required
        self.default = default
        self.help_text = help_text
        self.choices = choices  # List of valid choices
        self.nargs = nargs  # '+', '*', or number
        self.action = action  # 'store_true', 'store_false', etc.

    def is_file_argument(self):
        """Detect if this argument should be treated as a file path"""
        file_keywords = ['file', 'path', 'input', 'output', 'reference', 'source', 'sources']
        name_lower = self.name.lower()
        return any(keyword in name_lower for keyword in file_keywords)

    def is_directory_argument(self):
        """Detect if this argument should be treated as a directory path"""
        dir_keywords = ['dir', 'directory', 'folder']
        name_lower = self.name.lower()
        return any(keyword in name_lower for keyword in dir_keywords)

    def is_multiple(self):
        """Check if this argument accepts multiple values"""
        return self.nargs in ['+', '*'] or (isinstance(self.nargs, int) and self.nargs > 1)


class ScriptAnalyzer:
    """Analyzes a Python script to extract argparse argument definitions"""

    def __init__(self, script_path):
        self.script_path = script_path
        self.arguments = []

    def analyze(self):
        """Parse the script and extract argument information"""
        with open(self.script_path, 'r') as f:
            source = f.read()

        try:
            tree = ast.parse(source)
            self._visit_ast(tree)
        except SyntaxError as e:
            print(f"Error parsing script: {e}")
            return []

        return self.arguments

    def _visit_ast(self, node):
        """Recursively visit AST nodes to find argparse calls"""
        for child in ast.walk(node):
            # Look for parser.add_argument() calls
            if isinstance(child, ast.Call):
                if self._is_add_argument_call(child):
                    arg_info = self._extract_argument_info(child)
                    if arg_info:
                        self.arguments.append(arg_info)

    def _is_add_argument_call(self, node):
        """Check if this is a parser.add_argument() call"""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == 'add_argument'
        return False

    def _extract_argument_info(self, call_node):
        """Extract argument details from add_argument() call"""
        # Get the argument name (first positional argument)
        if not call_node.args:
            return None

        # Handle both short and long form: add_argument('-r', '--reference', ...)
        arg_names = []
        for arg in call_node.args:
            if isinstance(arg, ast.Constant):
                arg_names.append(arg.value)

        if not arg_names:
            return None

        # Prefer the long form (--name) over short form (-n)
        arg_name = None
        for name in arg_names:
            if name.startswith('--'):
                arg_name = name[2:]  # Remove '--' prefix
                break
        if not arg_name and arg_names:
            arg_name = arg_names[0].lstrip('-')

        # Extract keyword arguments
        kwargs = {}
        for keyword in call_node.keywords:
            key = keyword.arg
            value = self._extract_value(keyword.value)
            kwargs[key] = value

        # Use 'dest' if specified (for args like --no-crossfade with dest='crossfade')
        if 'dest' in kwargs:
            arg_name = kwargs['dest']

        # Build ArgumentInfo
        arg_type = self._determine_type(kwargs)
        required = kwargs.get('required', False)
        default = kwargs.get('default')
        help_text = kwargs.get('help', '')
        choices = kwargs.get('choices')
        nargs = kwargs.get('nargs')
        action = kwargs.get('action')

        return ArgumentInfo(
            name=arg_name,
            arg_type=arg_type,
            required=required,
            default=default,
            help_text=help_text,
            choices=choices,
            nargs=nargs,
            action=action
        )

    def _extract_value(self, node):
        """Extract Python value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._extract_value(elt) for elt in node.elts]
        elif isinstance(node, ast.Name):
            # Handle references like type=str, type=int
            if node.id in ['str', 'int', 'float', 'bool']:
                return node.id
            return None
        elif isinstance(node, ast.Attribute):
            # Handle things like action='store_true'
            return None
        else:
            return None

    def _determine_type(self, kwargs):
        """Determine the argument type from kwargs"""
        # Check action first (for boolean flags)
        action = kwargs.get('action')
        if action in ['store_true', 'store_false']:
            return 'bool'

        # Check if it has choices (should be dropdown) - prioritize this
        if kwargs.get('choices'):
            return 'choice'

        # Check explicit type
        arg_type = kwargs.get('type')
        if arg_type == 'int':
            return 'int'
        elif arg_type == 'float':
            return 'float'
        elif arg_type == 'str':
            return 'str'

        # Default to string
        return 'str'


class GUIGenerator:
    """Generates a tkinter GUI for a script's arguments"""

    def __init__(self, script_path, arguments):
        self.script_path = script_path
        self.arguments = arguments
        self.root = tk.Tk()
        self.widgets = {}  # Map argument name to widget
        self.values = {}   # Map argument name to StringVar/IntVar/etc

    def create_gui(self):
        """Create the GUI window - SIMPLIFIED VERSION WITHOUT CANVAS"""
        script_name = Path(self.script_path).name
        self.root.title(f"GUI Wrapper - {script_name}")
        self.root.geometry("1000x800")
        self.root.configure(bg='white')

        # Header
        header = tk.Label(self.root, text=f"Configure: {script_name}",
                         font=('Arial', 14, 'bold'), bg='white', fg='black', pady=10)
        header.pack(fill=tk.X)

        # Separator
        sep1 = tk.Frame(self.root, height=2, bg='#cccccc')
        sep1.pack(fill=tk.X)

        # Arguments section - simple frame with scrollbar (no canvas!)
        args_container = tk.Frame(self.root, bg='white')
        args_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create a frame that will hold all argument widgets
        args_frame = tk.Frame(args_container, bg='white')
        args_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create widgets for each argument - using pack instead of grid
        for i, arg in enumerate(self.arguments):
            self._create_argument_widget_pack(args_frame, arg)

        # Separator
        sep2 = tk.Frame(self.root, height=2, bg='#cccccc')
        sep2.pack(fill=tk.X)

        # Bottom section: Buttons and output
        bottom_frame = tk.Frame(self.root, bg='white')
        bottom_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        # Run button
        button_frame = tk.Frame(bottom_frame, bg='white')
        button_frame.pack(fill=tk.X, pady=(0, 10))

        run_button = tk.Button(button_frame, text="▶ Run Script", command=self._run_script,
                              bg='#4CAF50', fg='white', font=('Arial', 14, 'bold'),
                              padx=30, pady=10)
        run_button.pack(side=tk.LEFT, padx=5)

        clear_button = tk.Button(button_frame, text="Clear Output", command=self._clear_output,
                                bg='#FF9800', fg='white', font=('Arial', 12),
                                padx=15, pady=10)
        clear_button.pack(side=tk.LEFT, padx=5)

        # Output area
        output_label = tk.Label(bottom_frame, text="Output:", anchor='w',
                               font=('Arial', 12, 'bold'), bg='white', fg='black')
        output_label.pack(fill=tk.X, pady=(0, 5))

        self.output_text = scrolledtext.ScrolledText(bottom_frame, height=10, wrap=tk.WORD,
                                                     bg='#2b2b2b', fg='#00ff00',
                                                     font=('Courier', 11),
                                                     insertbackground='white')
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Force initial render
        self.root.update()

    def _create_argument_widget_pack(self, parent, arg):
        """Create appropriate widget for an argument - USING PACK (NO CANVAS)"""
        # Container for this argument with visible border
        container = tk.Frame(parent, bg='white', relief=tk.RAISED, borderwidth=2)
        container.pack(fill=tk.X, padx=5, pady=5)

        # Label row
        label_frame = tk.Frame(container, bg='white')
        label_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        label_text = arg.name.replace('-', ' ').title()
        if arg.required:
            label_text += " *"

        label = tk.Label(label_frame, text=label_text, anchor='w',
                        bg='white', fg='black', font=('Arial', 11, 'bold'))
        label.pack(side=tk.LEFT)

        # Help text on its own row if present
        if arg.help_text:
            help_frame = tk.Frame(container, bg='white')
            help_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
            help_label = tk.Label(help_frame, text=arg.help_text, fg='#666666',
                                 font=('Arial', 9), bg='white', anchor='w', wraplength=800)
            help_label.pack(fill=tk.X)

        # Widget row
        widget_frame = tk.Frame(container, bg='white')
        widget_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Create appropriate widget based on type
        if arg.arg_type == 'bool':
            var = tk.BooleanVar(value=arg.default if arg.default is not None else False)
            widget = tk.Checkbutton(widget_frame, variable=var, bg='white', fg='black',
                                   selectcolor='white', activebackground='white',
                                   font=('Arial', 10))
            widget.pack(side=tk.LEFT)
            self.values[arg.name] = var

        elif arg.choices:
            var = tk.StringVar(value=arg.default if arg.default else (arg.choices[0] if arg.choices else ''))
            widget = tk.OptionMenu(widget_frame, var, *arg.choices)
            widget.config(width=20, bg='white', fg='black', activebackground='#e0e0e0',
                         font=('Arial', 10))
            menu = widget['menu']
            menu.config(bg='white', fg='black', font=('Arial', 10))
            widget.pack(side=tk.LEFT, padx=5)
            self.values[arg.name] = var

        elif arg.is_file_argument() and arg.is_multiple():
            var = tk.StringVar(value='')
            self.values[arg.name] = var

            listbox = tk.Listbox(widget_frame, height=3, width=60, bg='white', fg='black',
                                font=('Arial', 10))
            listbox.pack(side=tk.LEFT, padx=5)

            btn_frame = tk.Frame(widget_frame, bg='white')
            btn_frame.pack(side=tk.LEFT, padx=5)

            def add_file():
                files = filedialog.askopenfilenames(title=f"Select {arg.name}")
                for file in files:
                    listbox.insert(tk.END, file)
                self._update_file_list(arg.name, listbox, var)

            def remove_file():
                selection = listbox.curselection()
                for index in reversed(selection):
                    listbox.delete(index)
                self._update_file_list(arg.name, listbox, var)

            tk.Button(btn_frame, text="Add Files", command=add_file,
                     bg='#4CAF50', fg='white', font=('Arial', 10), padx=10).pack(pady=2)
            tk.Button(btn_frame, text="Remove", command=remove_file,
                     bg='#f44336', fg='white', font=('Arial', 10), padx=10).pack(pady=2)

            self.widgets[arg.name] = listbox

        elif arg.is_directory_argument():
            var = tk.StringVar(value=arg.default if arg.default else '')
            entry = tk.Entry(widget_frame, textvariable=var, width=60, bg='white', fg='black',
                           insertbackground='black', font=('Arial', 10))
            entry.pack(side=tk.LEFT, padx=5)

            def browse_dir():
                dirname = filedialog.askdirectory(title=f"Select {arg.name}")
                if dirname:
                    var.set(dirname)

            browse_btn = tk.Button(widget_frame, text="Browse...", command=browse_dir,
                                  bg='#2196F3', fg='white', font=('Arial', 10), padx=15)
            browse_btn.pack(side=tk.LEFT, padx=5)

            self.values[arg.name] = var

        elif arg.is_file_argument():
            var = tk.StringVar(value=arg.default if arg.default else '')
            entry = tk.Entry(widget_frame, textvariable=var, width=60, bg='white', fg='black',
                           insertbackground='black', font=('Arial', 10))
            entry.pack(side=tk.LEFT, padx=5)

            def browse():
                if 'output' in arg.name.lower():
                    filename = filedialog.asksaveasfilename(title=f"Select {arg.name}")
                else:
                    filename = filedialog.askopenfilename(title=f"Select {arg.name}")
                if filename:
                    var.set(filename)

            browse_btn = tk.Button(widget_frame, text="Browse...", command=browse,
                                  bg='#2196F3', fg='white', font=('Arial', 10), padx=15)
            browse_btn.pack(side=tk.LEFT, padx=5)

            self.values[arg.name] = var

        else:
            # Regular text entry for strings, ints, floats
            var = tk.StringVar(value=str(arg.default) if arg.default is not None else '')
            entry = tk.Entry(widget_frame, textvariable=var, width=40, bg='white', fg='black',
                           insertbackground='black', font=('Arial', 10))
            entry.pack(side=tk.LEFT, padx=5)
            self.values[arg.name] = var

    def _create_argument_widget(self, parent, arg, row):
        """Create appropriate widget for an argument - GRID VERSION"""
        frame = tk.Frame(parent, bg='white', pady=5, padx=5)
        frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=2, padx=5)
        frame.columnconfigure(1, weight=1)

        # Label with help text - EXPLICIT COLORS FOR VISIBILITY
        label_text = arg.name.replace('-', ' ').title()
        if arg.required:
            label_text += " *"
        label = tk.Label(frame, text=label_text, width=20, anchor='w',
                        bg='white', fg='black', font=('Arial', 10, 'bold'))
        label.grid(row=0, column=0, sticky=tk.W, padx=5)

        # Add help text as tooltip (simplified - just show in label)
        if arg.help_text:
            help_label = tk.Label(frame, text=arg.help_text, fg='#555555',
                                 font=('Arial', 9), bg='white', anchor='w')
            help_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5)

        # Create appropriate widget based on type - ALL WITH EXPLICIT COLORS
        if arg.arg_type == 'bool':
            var = tk.BooleanVar(value=arg.default if arg.default is not None else False)
            widget = tk.Checkbutton(frame, variable=var, bg='white', fg='black',
                                   selectcolor='white', activebackground='white')
            widget.grid(row=0, column=1, sticky=tk.W)
            self.values[arg.name] = var

        elif arg.choices:
            var = tk.StringVar(value=arg.default if arg.default else (arg.choices[0] if arg.choices else ''))
            # Use OptionMenu instead of Combobox for better compatibility
            widget = tk.OptionMenu(frame, var, *arg.choices)
            widget.config(width=15, bg='white', fg='black', activebackground='#e0e0e0')
            # Also style the menu
            menu = widget['menu']
            menu.config(bg='white', fg='black')
            widget.grid(row=0, column=1, sticky=tk.W, padx=5)
            self.values[arg.name] = var

        elif arg.is_file_argument() and arg.is_multiple():
            # Multiple files - use listbox with add/remove buttons
            var = tk.StringVar(value='')
            self.values[arg.name] = var

            listbox_frame = tk.Frame(frame, bg='white')
            listbox_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
            listbox_frame.columnconfigure(0, weight=1)

            listbox = tk.Listbox(listbox_frame, height=3, width=40, bg='white', fg='black')
            listbox.grid(row=0, column=0, sticky=(tk.W, tk.E))

            btn_frame = tk.Frame(listbox_frame, bg='white')
            btn_frame.grid(row=0, column=1, padx=5)

            def add_file():
                files = filedialog.askopenfilenames(title=f"Select {arg.name}")
                for file in files:
                    listbox.insert(tk.END, file)
                self._update_file_list(arg.name, listbox, var)

            def remove_file():
                selection = listbox.curselection()
                for index in reversed(selection):
                    listbox.delete(index)
                self._update_file_list(arg.name, listbox, var)

            tk.Button(btn_frame, text="Add Files", command=add_file, bg='#4CAF50', fg='white').pack(pady=2, fill=tk.X)
            tk.Button(btn_frame, text="Remove", command=remove_file, bg='#f44336', fg='white').pack(pady=2, fill=tk.X)

            self.widgets[arg.name] = listbox

        elif arg.is_directory_argument():
            # Directory - use entry with browse button
            var = tk.StringVar(value=arg.default if arg.default else '')
            entry = tk.Entry(frame, textvariable=var, width=50, bg='white', fg='black',
                           insertbackground='black')
            entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

            def browse_dir():
                dirname = filedialog.askdirectory(title=f"Select {arg.name}")
                if dirname:
                    var.set(dirname)

            browse_btn = tk.Button(frame, text="Browse...", command=browse_dir,
                                  bg='#2196F3', fg='white')
            browse_btn.grid(row=0, column=2, padx=5)

            self.values[arg.name] = var

        elif arg.is_file_argument():
            # Single file - use entry with browse button
            var = tk.StringVar(value=arg.default if arg.default else '')
            entry = tk.Entry(frame, textvariable=var, width=50, bg='white', fg='black',
                           insertbackground='black')
            entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

            def browse():
                if 'output' in arg.name.lower():
                    filename = filedialog.asksaveasfilename(title=f"Select {arg.name}")
                else:
                    filename = filedialog.askopenfilename(title=f"Select {arg.name}")
                if filename:
                    var.set(filename)

            browse_btn = tk.Button(frame, text="Browse...", command=browse,
                                  bg='#2196F3', fg='white')
            browse_btn.grid(row=0, column=2, padx=5)

            self.values[arg.name] = var

        else:
            # Regular text entry for strings, ints, floats
            var = tk.StringVar(value=str(arg.default) if arg.default is not None else '')
            entry = tk.Entry(frame, textvariable=var, width=30, bg='white', fg='black',
                           insertbackground='black')
            entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
            self.values[arg.name] = var

    def _update_file_list(self, arg_name, listbox, var):
        """Update the StringVar with space-separated file list"""
        files = [listbox.get(i) for i in range(listbox.size())]
        var.set(' '.join(f'"{f}"' for f in files))

    def _run_script(self):
        """Execute the wrapped script with collected arguments"""
        # Validate required fields first
        missing_fields = []
        for arg in self.arguments:
            if arg.required:
                value = self.values[arg.name].get()
                if not value or (isinstance(value, str) and not value.strip()):
                    missing_fields.append(arg.name)

        if missing_fields:
            from tkinter import messagebox
            messagebox.showerror(
                "Missing Required Fields",
                f"Please fill in the following required fields:\n\n" +
                "\n".join(f"  • {field}" for field in missing_fields)
            )
            return

        # Build command line
        cmd = [sys.executable, self.script_path]

        for arg in self.arguments:
            value = self.values[arg.name].get()

            # Skip if empty and not required
            if not value and not arg.required:
                continue

            # Handle boolean flags
            if arg.arg_type == 'bool':
                if value:  # Only add flag if True
                    cmd.append(f'--{arg.name}')
                continue

            # Handle multiple files (already formatted with quotes)
            if arg.is_file_argument() and arg.is_multiple():
                if value:
                    # Value is already space-separated with quotes
                    cmd.append(f'--{arg.name}')
                    # Parse the quoted strings
                    import shlex
                    files = shlex.split(value)
                    cmd.extend(files)
                continue

            # Handle regular arguments
            if value:
                cmd.append(f'--{arg.name}')
                cmd.append(value)

        # Display command
        self._clear_output()
        self.output_text.insert(tk.END, f"Running: {' '.join(cmd)}\n\n")
        self.output_text.see(tk.END)

        # Run in separate thread to avoid blocking GUI
        thread = threading.Thread(target=self._execute_command, args=(cmd,))
        thread.daemon = True
        thread.start()

    def _execute_command(self, cmd):
        """Execute command and capture output"""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Stream output
            for line in process.stdout:
                self.root.after(0, self._append_output, line)

            process.wait()

            if process.returncode == 0:
                self.root.after(0, self._append_output, "\n--- Completed successfully ---\n")
            else:
                self.root.after(0, self._append_output, f"\n--- Exited with code {process.returncode} ---\n")

        except Exception as e:
            self.root.after(0, self._append_output, f"\nError: {str(e)}\n")

    def _append_output(self, text):
        """Append text to output (called from main thread)"""
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)

    def _clear_output(self):
        """Clear the output text area"""
        self.output_text.delete(1.0, tk.END)

    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


def generate_gui_wrapper(script_path):
    """Main function to generate and run GUI wrapper"""
    # Analyze the script
    print(f"Analyzing {script_path}...")
    analyzer = ScriptAnalyzer(script_path)
    arguments = analyzer.analyze()

    if not arguments:
        print("No arguments found in script!")
        return

    print(f"Found {len(arguments)} arguments:")
    for arg in arguments:
        print(f"  - {arg.name} ({arg.arg_type}){' [required]' if arg.required else ''}")

    # Create and run GUI
    print("\nLaunching GUI...")
    gui = GUIGenerator(script_path, arguments)
    gui.create_gui()
    gui.run()


def main():
    if len(sys.argv) != 2:
        print("Usage: python script-ui.py <target_script.py>")
        print("\nExample:")
        print("  python script-ui.py ../music/llm-generated/tuned-mosaic.py")
        sys.exit(1)

    script_path = sys.argv[1]

    if not Path(script_path).exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    generate_gui_wrapper(script_path)


if __name__ == '__main__':
    main()
