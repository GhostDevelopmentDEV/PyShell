import os
import shutil
import sys
import platform
import datetime
import subprocess
import re
import threading
import customtkinter as ctk
from tkinter import Text, Scrollbar, END, INSERT, SEL, N, S, E, W, messagebox, filedialog, StringVar, Menu, Toplevel, Label, Entry, Button, Frame, Tk

# Appearance settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ===================== TECHNICAL INFORMATION =====================
class AppInfo:
    # Necessary information
    app_name = "PyShell"
    app_version = 1.3
    app_version_year = 2026
    app_dev = "GhostDEV (GhostDevelopmentDEV)"
    # Additional Info
    app_version_state = "Release"
    app_dev_nickname = "GhostDEV"
    app_dev_full_nickname = "GhostDevelopmentDEV"
    app_dev_github_link = "https://github.com/GhostDevelopmentDEV/"

# Color constants for text
COLORS = {
    "info": "#00bfff",       # bright blue
    "success": "#00ff00",    # green
    "error": "#ff4444",      # red
    "warning": "#ffff00",    # yellow
    "prompt": "#ff8800",     # orange
    "output": "#dddddd",     # light grey
    "user_input": "#ffffff", # white
    "folder": "#ffaa00",     # gold
    "file": "#88ff88",
    "command": "#64d382"     # light green
}

# Glyphs for the interface
GLYPHS = {
    "prompt": "❯",
    "folder": "📁",
    "file": "📄",
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "divider": "─",
    "time": "🕒",
    "date": "📅",
    "calc": "🧮",
    "search": "🔍",
    "edit": "✏️"
}

# ===================== TEXT EDITOR =====================

class TextEditorWindow(ctk.CTkToplevel):
    def __init__(self, parent, filename=None):
        super().__init__(parent)
        self.title(f"Text Editor - {filename}" if filename else "Untitled - Text Editor")
        self.geometry("1000x700")
        self.filename = filename
        self.unsaved_changes = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True)

        # Line numbers and text area
        self.create_line_numbers(main_frame)
        self.create_text_area(main_frame)
        self.create_status_bar()
        self.create_menu()

        # Syntax highlighting
        self.syntax_highlighting = True
        self.last_highlight = ""

        # Load file
        if filename and os.path.exists(filename):
            self.load_file(filename)
        else:
            self.text_area.insert("1.0", "")
            if filename:
                self.status_var.set(f"New file: {filename}")

        # Bind shortcuts
        self.bind_shortcuts()

        # Track changes
        self.text_area.bind("<<Modified>>", self.on_text_modified)
        self.text_area.bind("<KeyRelease>", self.update_line_numbers)
        self.text_area.bind("<ButtonRelease-1>", self.update_line_numbers)
        self.text_area.bind("<MouseWheel>", self.on_mousewheel)
        self.text_area.bind("<Configure>", self.on_configure)

        self.focus_set()
        self.update_line_numbers()

    def create_line_numbers(self, parent):
        """Create the line numbers area"""
        self.line_numbers = Text(
            parent,
            width=4,
            padx=4,
            takefocus=0,
            border=0,
            background="#2b2b2b",
            foreground="#888888",
            font=("Cascadia Mono", 12),
            state="disabled",
            wrap="none"
        )
        self.line_numbers.pack(side="left", fill="y")

    def create_text_area(self, parent):
        """Create the main text area"""
        self.text_area = Text(
            parent,
            font=("Cascadia Mono", 12),
            bg="#2b2b2b",
            fg="#f0f0f0",
            insertbackground="#ffffff",
            selectbackground="#3d3d3d",
            padx=10,
            pady=10,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=-1
        )
        self.text_area.pack(side="right", fill="both", expand=True)

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(parent, command=self.text_area.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_area.config(yscrollcommand=scrollbar.set)

    def create_status_bar(self):
        """Create the status bar"""
        self.status_var = StringVar(value="Ready")
        status_bar = ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            anchor="w",
            padx=10,
            font=("Cascadia Mono", 10),
            height=25
        )
        status_bar.pack(fill="x", side="bottom")

    def create_menu(self):
        """Create the menu"""
        menubar = Menu(self)
        self.config(menu=menubar)

        # File
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close, accelerator="Ctrl+Q")

        # Edit
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", command=self.find, accelerator="Ctrl+F")
        edit_menu.add_command(label="Replace", command=self.replace, accelerator="Ctrl+H")

        # View
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Syntax Highlighting", command=self.toggle_highlighting, variable=StringVar(value=self.syntax_highlighting))

        # Help
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_as())
        self.bind("<Control-q>", lambda e: self.on_close())
        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-x>", lambda e: self.cut())
        self.bind("<Control-c>", lambda e: self.copy())
        self.bind("<Control-v>", lambda e: self.paste())
        self.bind("<Control-f>", lambda e: self.find())
        self.bind("<Control-h>", lambda e: self.replace())

    # ---------- File operations ----------
    def load_file(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete("1.0", END)
            self.text_area.insert("1.0", content)
            self.filename = filename
            self.unsaved_changes = False
            self.status_var.set(f"Loaded: {filename}")
            self.title(f"Text Editor - {filename}")
            self.update_line_numbers()
            if self.syntax_highlighting:
                self.highlight_syntax()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def new_file(self):
        if self.unsaved_changes:
            if not self.ask_save_changes():
                return
        self.text_area.delete("1.0", END)
        self.filename = None
        self.unsaved_changes = False
        self.title("Untitled - Text Editor")
        self.status_var.set("New file")
        self.update_line_numbers()

    def open_file(self):
        if self.unsaved_changes:
            if not self.ask_save_changes():
                return
        filename = filedialog.askopenfilename(
            title="Open File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.load_file(filename)

    def save_file(self, event=None):
        if not self.filename:
            return self.save_as()
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(self.text_area.get("1.0", END))
            self.unsaved_changes = False
            self.status_var.set(f"Saved: {self.filename}")
            self.title(f"Text Editor - {self.filename}")
            return "break"
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            return "break"

    def save_as(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.filename = filename
            return self.save_file()
        return "break"

    def ask_save_changes(self):
        response = messagebox.askyesnocancel("Unsaved Changes", "Do you want to save changes?")
        if response is None:
            return False
        if response:
            self.save_file()
        return True

    def on_close(self):
        if self.unsaved_changes:
            if not self.ask_save_changes():
                return
        self.destroy()

    # ---------- Editing ----------
    def undo(self):
        try:
            self.text_area.edit_undo()
            self.update_line_numbers()
            if self.syntax_highlighting:
                self.highlight_syntax()
        except:
            pass

    def redo(self):
        try:
            self.text_area.edit_redo()
            self.update_line_numbers()
            if self.syntax_highlighting:
                self.highlight_syntax()
        except:
            pass

    def cut(self):
        self.text_area.event_generate("<<Cut>>")

    def copy(self):
        self.text_area.event_generate("<<Copy>>")

    def paste(self):
        self.text_area.event_generate("<<Paste>>")
        if self.syntax_highlighting:
            self.highlight_syntax()

    # ---------- Find and replace ----------
    def find(self):
        self.find_dialog = FindReplaceDialog(self, find_only=True)

    def replace(self):
        self.replace_dialog = FindReplaceDialog(self, find_only=False)

    # ---------- Syntax highlighting ----------
    def toggle_highlighting(self):
        self.syntax_highlighting = not self.syntax_highlighting
        if self.syntax_highlighting:
            self.highlight_syntax()
        else:
            self.clear_syntax_highlighting()

    def clear_syntax_highlighting(self):
        for tag in self.text_area.tag_names():
            if tag.startswith("hl_"):
                self.text_area.tag_delete(tag)

    def highlight_syntax(self):
        """Simple syntax highlighting for Python, C, JavaScript, etc."""
        if not self.syntax_highlighting:
            return
        self.clear_syntax_highlighting()
        content = self.text_area.get("1.0", END)
        # Determine language by file extension
        ext = os.path.splitext(self.filename)[1].lower() if self.filename else ""
        if ext in (".py", ".pyw"):
            self.highlight_python(content)
        elif ext in (".c", ".h"):
            self.highlight_c(content)
        elif ext in (".js", ".mjs"):
            self.highlight_javascript(content)
        elif ext in (".html", ".htm"):
            self.highlight_html(content)
        else:
            # Other languages can be added
            pass

    def highlight_python(self, content):
        # Python keywords
        keywords = ["and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"]
        self._highlight_patterns(keywords, "hl_keyword", "#569cd6")
        # Strings
        self._highlight_regex(r'".*?"', "hl_string", "#ce9178")
        self._highlight_regex(r"'.*?'", "hl_string", "#ce9178")
        # Comments
        self._highlight_regex(r"#.*$", "hl_comment", "#6a9955")
        # Numbers
        self._highlight_regex(r"\b\d+\b", "hl_number", "#b5cea8")

    def highlight_c(self, content):
        keywords = ["auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum", "extern", "float", "for", "goto", "if", "int", "long", "register", "return", "short", "signed", "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while"]
        self._highlight_patterns(keywords, "hl_keyword", "#569cd6")
        self._highlight_regex(r'".*?"', "hl_string", "#ce9178")
        self._highlight_regex(r"//.*$", "hl_comment", "#6a9955")
        self._highlight_regex(r"/\*.*?\*/", "hl_comment", "#6a9955", re.DOTALL)
        self._highlight_regex(r"\b\d+\b", "hl_number", "#b5cea8")

    def highlight_javascript(self, content):
        keywords = ["break", "case", "catch", "class", "const", "continue", "debugger", "default", "delete", "do", "else", "export", "extends", "finally", "for", "function", "if", "import", "in", "instanceof", "new", "return", "super", "switch", "this", "throw", "try", "typeof", "var", "void", "while", "with", "yield"]
        self._highlight_patterns(keywords, "hl_keyword", "#569cd6")
        self._highlight_regex(r'".*?"', "hl_string", "#ce9178")
        self._highlight_regex(r"'.*?'", "hl_string", "#ce9178")
        self._highlight_regex(r"//.*$", "hl_comment", "#6a9955")
        self._highlight_regex(r"/\*.*?\*/", "hl_comment", "#6a9955", re.DOTALL)
        self._highlight_regex(r"\b\d+\b", "hl_number", "#b5cea8")

    def highlight_html(self, content):
        self._highlight_regex(r"<[^>]+>", "hl_tag", "#569cd6")
        self._highlight_regex(r"<!--.*?-->", "hl_comment", "#6a9955", re.DOTALL)

    def _highlight_patterns(self, patterns, tag_name, color):
        """Highlight exact words"""
        self.text_area.tag_config(tag_name, foreground=color)
        for pattern in patterns:
            start = "1.0"
            while True:
                start = self.text_area.search(r"\b" + pattern + r"\b", start, stopindex=END, regexp=True)
                if not start:
                    break
                end = f"{start}+{len(pattern)}c"
                self.text_area.tag_add(tag_name, start, end)
                start = end

    def _highlight_regex(self, pattern, tag_name, color, flags=0):
        """Highlight using regular expressions"""
        self.text_area.tag_config(tag_name, foreground=color)
        regex = re.compile(pattern, flags)
        content = self.text_area.get("1.0", END)
        for match in regex.finditer(content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text_area.tag_add(tag_name, start, end)

    # ---------- Line numbers ----------
    def update_line_numbers(self, event=None):
        """Update line numbers"""
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", END)
        line_count = int(self.text_area.index("end-1c").split(".")[0])
        numbers = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.config(state="disabled")

    def on_mousewheel(self, event):
        """Synchronize line numbers scrolling"""
        self.line_numbers.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_configure(self, event):
        """When window size changes"""
        self.update_line_numbers()

    def on_text_modified(self, event):
        if self.text_area.edit_modified():
            self.unsaved_changes = True
            self.status_var.set(f"Modified: {self.filename}" if self.filename else "Modified")
            self.text_area.edit_modified(False)
            if self.syntax_highlighting:
                self.highlight_syntax()

    def show_about(self):
        messagebox.showinfo("About", "Text Editor v1.0\nA simple text editor with syntax highlighting.\nBuilt with Python and customtkinter.")

# ===================== FIND/REPLACE DIALOG =====================

class FindReplaceDialog(ctk.CTkToplevel):
    def __init__(self, parent, find_only=True):
        super().__init__(parent)
        self.parent = parent
        self.find_only = find_only
        self.title("Find" if find_only else "Find and Replace")
        self.geometry("400x200")
        self.resizable(False, False)
        self.grab_set()

        # Variables
        self.find_var = StringVar()
        self.replace_var = StringVar()
        self.case_sensitive = BooleanVar(value=False)
        self.whole_word = BooleanVar(value=False)
        self.wrap_around = BooleanVar(value=True)

        # Widgets
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def create_widgets(self):
        # Find
        label_find = ctk.CTkLabel(self, text="Find:")
        label_find.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        entry_find = ctk.CTkEntry(self, textvariable=self.find_var)
        entry_find.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        entry_find.focus()

        # Replace (if needed)
        if not self.find_only:
            label_replace = ctk.CTkLabel(self, text="Replace with:")
            label_replace.grid(row=1, column=0, padx=10, pady=10, sticky="e")
            entry_replace = ctk.CTkEntry(self, textvariable=self.replace_var)
            entry_replace.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        # Options
        opt_frame = ctk.CTkFrame(self)
        opt_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        ctk.CTkCheckBox(opt_frame, text="Case sensitive", variable=self.case_sensitive).pack(anchor="w")
        ctk.CTkCheckBox(opt_frame, text="Whole word", variable=self.whole_word).pack(anchor="w")
        ctk.CTkCheckBox(opt_frame, text="Wrap around", variable=self.wrap_around).pack(anchor="w")

        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        btn_find = ctk.CTkButton(btn_frame, text="Find", command=self.find_next)
        btn_find.pack(side="left", padx=5)
        if not self.find_only:
            btn_replace = ctk.CTkButton(btn_frame, text="Replace", command=self.replace_current)
            btn_replace.pack(side="left", padx=5)
            btn_replace_all = ctk.CTkButton(btn_frame, text="Replace All", command=self.replace_all)
            btn_replace_all.pack(side="left", padx=5)
        btn_close = ctk.CTkButton(btn_frame, text="Close", command=self.destroy)
        btn_close.pack(side="right", padx=5)

        self.columnconfigure(1, weight=1)

    def find_next(self):
        text = self.find_var.get()
        if not text:
            return
        start = self.parent.text_area.index(INSERT)
        if not self.wrap_around.get():
            start = self.parent.text_area.index(INSERT)
        else:
            start = "1.0"  # Start from beginning
        # Search
        match = self._search(text, start)
        if match:
            self.parent.text_area.tag_remove("sel", "1.0", END)
            self.parent.text_area.tag_add("sel", match[0], match[1])
            self.parent.text_area.mark_set(INSERT, match[1])
            self.parent.text_area.see(INSERT)
        else:
            messagebox.showinfo("Find", f"'{text}' not found.")

    def _search(self, pattern, start):
        """Search for text with options"""
        flags = 0
        if not self.case_sensitive.get():
            flags |= re.IGNORECASE
        if self.whole_word.get():
            pattern = r"\b" + re.escape(pattern) + r"\b"
        else:
            pattern = re.escape(pattern)
        # Search
        pos = self.parent.text_area.search(pattern, start, stopindex=END, regexp=True, nocase=not self.case_sensitive.get())
        if pos:
            end = f"{pos}+{len(self.find_var.get())}c"
            return (pos, end)
        return None

    def replace_current(self):
        text = self.find_var.get()
        if not text:
            return
        # If there's a selection, replace only if it matches the search text
        sel = self.parent.text_area.tag_ranges(SEL)
        if sel:
            start, end = sel[0], sel[1]
            selected = self.parent.text_area.get(start, end)
            # Check match with options
            if self._match(selected, text):
                self.parent.text_area.delete(start, end)
                self.parent.text_area.insert(start, self.replace_var.get())
                self.parent.text_area.tag_remove("sel", "1.0", END)
                # Find next occurrence
                self.find_next()
                return
        # If no selection, just find next
        self.find_next()

    def replace_all(self):
        text = self.find_var.get()
        if not text:
            return
        count = 0
        start = "1.0"
        while True:
            match = self._search(text, start)
            if not match:
                break
            start, end = match
            self.parent.text_area.delete(start, end)
            self.parent.text_area.insert(start, self.replace_var.get())
            count += 1
            start = f"{start}+{len(self.replace_var.get())}c"
        messagebox.showinfo("Replace All", f"Replaced {count} occurrence(s).")

    def _match(self, text, pattern):
        """Compare text with pattern considering options"""
        if not self.case_sensitive.get():
            return text.lower() == pattern.lower()
        else:
            return text == pattern

# ===================== TERMINAL =====================

class TerminalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PyShell Terminal")
        self.geometry("1000x570")

        # Font settings
        self.font = ("Cascadia Mono", 12)

        # Current directory
        self.current_dir = os.getcwd()
        self.username = os.getlogin()
        self.hostname = platform.node()
        self.session_start = datetime.datetime.now()

        # Command history
        self.command_history = []
        self.history_index = -1
        self.input_start = "1.0"

        # Create interface
        self.create_widgets()

        # Update prompt
        self.update_prompt()
        self.insert_prompt()

        # Register commands
        self.commands = {
            'help': self.show_help,
            'about': self.show_about,
            'ls': self.list_dir,
            'dir': self.list_dir,
            'cd': self.change_dir,
            'pwd': self.print_work_dir,
            'mkdir': self.make_dir,
            'rmdir': self.remove_dir,
            'rm': self.remove_file,
            'cp': self.copy_file,
            'mv': self.move_file,
            'cat': self.cat_file,
            'echo': self.echo_text,
            'clear': self.clear_screen,
            'exit': self.exit_shell,
            'ps': self.list_processes,
            'sysinfo': self.system_info,
            'find': self.find_files,
            'size': self.file_size,
            'time': self.show_time,
            'tree': self.show_tree,
            'rename': self.rename_file,
            'grep': self.grep_text,
            'zip': self.zip_file,
            'unzip': self.unzip_file,
            'env': self.show_env,
            'setenv': self.set_env,
            'history': self.show_history,
            'calc': self.calculator,
            'edit': self.edit_file,
            'touch': self.touch_file,
            'tail': self.tail_file,
            'head': self.head_file,
            'wc': self.word_count,
            'sort': self.sort_file,
            'which': self.which_command,
        }

        # Status bar
        self.status_frame = ctk.CTkFrame(self, height=25, fg_color="#2b2b2b")
        self.status_frame.pack(fill="x", side="bottom")
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text=f"{GLYPHS['folder']} {self.current_dir} | {GLYPHS['time']} {datetime.datetime.now().strftime('%H:%M:%S')}",
            anchor="w",
            padx=10,
            font=("Cascadia Mono", 10),
            text_color="#aaaaaa"
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        # Update status every 2 seconds
        self.update_status()

    def create_widgets(self):
        # Main terminal text area
        self.terminal = Text(
            self,
            font=self.font,
            bg="#1e1e1e",
            fg="#f0f0f0",
            insertbackground="#ffffff",
            selectbackground="#3d3d3d",
            padx=10,
            pady=10,
            wrap="word",
            undo=True
        )
        self.terminal.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(self, command=self.terminal.yview)
        scrollbar.pack(side="right", fill="y")
        self.terminal.config(yscrollcommand=scrollbar.set)

        # Bind event handlers
        self.terminal.bind("<Return>", self.execute_command)
        self.terminal.bind("<Key>", self.on_key_press)
        self.terminal.bind("<BackSpace>", self.on_backspace)
        self.terminal.bind("<Up>", self.on_up_arrow)
        self.terminal.bind("<Down>", self.on_down_arrow)
        self.terminal.bind("<Home>", self.on_home)
        self.terminal.bind("<Tab>", self.auto_complete)

        # Prevent editing previous content
        self.terminal.mark_set("input_start", "1.0")
        self.terminal.mark_gravity("input_start", "left")

        # Focus on terminal
        self.terminal.focus_set()

        # Display welcome message
        self.print_output(f"{AppInfo.app_name} v{AppInfo.app_version} - Enhanced Terminal", COLORS["info"])
        self.print_output("Type 'help' for available commands", COLORS["info"])
        self.print_output("")

    def update_status(self):
        """Update status bar (current directory and time)"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.status_label.configure(
            text=f"{GLYPHS['folder']} {self.current_dir} | {GLYPHS['time']} {current_time}"
        )
        self.after(1000, self.update_status)

    def update_prompt(self):
        dir_name = os.path.basename(self.current_dir)
        if self.current_dir == os.path.expanduser("~"):
            dir_name = "~"
        prompt_text = f"{self.username}@{self.hostname} {dir_name}\n{GLYPHS['divider'] * (len(self.username) + len(self.hostname) + len(dir_name) + 2)}\n{GLYPHS['prompt']} "
        self.prompt = prompt_text

    def insert_prompt(self):
        """Insert prompt into terminal with color"""
        self.terminal.insert(END, self.prompt)
        start = self.terminal.index("end-{}c".format(len(self.prompt)))
        end = self.terminal.index("end")
        self.terminal.tag_add("prompt", start, end)
        self.terminal.tag_config("prompt", foreground=COLORS["prompt"])

        self.input_start = self.terminal.index(INSERT)
        self.terminal.mark_set("input_start", self.input_start)
        self.terminal.see(END)

    def print_output(self, text, color=None, tag_name=None):
        """Output text to terminal with optional color"""
        self.terminal.configure(state="normal")

        if color:
            tag_name = tag_name or f"color_{len(self.terminal.tag_names())}"
            start_pos = self.terminal.index(END)
            self.terminal.insert(END, text + "\n")
            end_pos = self.terminal.index(END)
            self.terminal.tag_add(tag_name, start_pos, end_pos)
            self.terminal.tag_config(tag_name, foreground=color)
        else:
            self.terminal.insert(END, text + "\n")

        self.terminal.mark_set(INSERT, END)
        self.terminal.see(END)
        self.terminal.configure(state="normal")

    def on_key_press(self, event):
        if self.terminal.compare(INSERT, "<", self.input_start):
            return "break"

    def on_backspace(self, event):
        if self.terminal.compare(INSERT, "==", self.input_start):
            return "break"
        if self.terminal.compare(INSERT, "<", self.input_start):
            return "break"
        return None

    def on_home(self, event):
        self.terminal.mark_set(INSERT, self.input_start)
        return "break"

    def on_up_arrow(self, event):
        if self.command_history:
            if self.history_index == -1:
                self.history_index = len(self.command_history) - 1
            elif self.history_index > 0:
                self.history_index -= 1

            self.terminal.delete(self.input_start, END)
            self.terminal.insert(self.input_start, self.command_history[self.history_index])
        return "break"

    def on_down_arrow(self, event):
        if self.command_history:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.terminal.delete(self.input_start, END)
                self.terminal.insert(self.input_start, self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.terminal.delete(self.input_start, END)
        return "break"

    def auto_complete(self, event):
        command = self.terminal.get(self.input_start, END).strip()
        parts = command.split()

        if not parts:
            return "break"

        # Command completion
        if len(parts) == 1:
            matches = [cmd for cmd in self.commands.keys() if cmd.startswith(parts[0])]
            if matches:
                self.terminal.delete(self.input_start, END)
                self.terminal.insert(self.input_start, matches[0])
                return "break"

        # File/directory completion
        last_part = parts[-1]
        dir_path = os.path.dirname(last_part) or self.current_dir
        base_name = os.path.basename(last_part)

        try:
            files = os.listdir(dir_path)
            matches = [f for f in files if f.startswith(base_name)]

            if matches:
                full_match = os.path.join(dir_path, matches[0])
                if os.path.isdir(full_match):
                    full_match += os.sep

                new_parts = parts[:-1] + [full_match]
                new_command = " ".join(new_parts)

                self.terminal.delete(self.input_start, END)
                self.terminal.insert(self.input_start, new_command)
                return "break"
        except:
            pass

        return "break"

    def execute_command(self, event):
        command = self.terminal.get(self.input_start, END).strip()

        if not command:
            self.insert_prompt()
            return "break"

        self.command_history.append(command)
        self.history_index = len(self.command_history)

        result = self.process_command(command)

        if result is not None:
            if isinstance(result, tuple):
                output_text, color = result
                self.print_output(output_text, color)
            else:
                self.print_output(result)

        self.update_prompt()
        self.insert_prompt()

        return "break"

    def process_command(self, command):
        cmd_parts = command.split()
        if not cmd_parts:
            return ""

        primary_cmd = cmd_parts[0].lower()
        args = cmd_parts[1:]

        if primary_cmd in self.commands:
            try:
                return self.commands[primary_cmd](args)
            except Exception as e:
                return f"{GLYPHS['error']} Error executing command: {str(e)}", COLORS["error"]
        else:
            return self.execute_system_command(command)

    # ============= SHELL COMMANDS =============

    def show_help(self, args):
        help_text = f"""
Available commands:

{GLYPHS['file']}/{GLYPHS['folder']} File operations:
  ls, dir      - List directory contents
  cd [path]    - Change directory
  pwd          - Print current directory
  mkdir [name] - Create directory
  rmdir [name] - Remove directory
  rm [file]    - Remove file
  cp [src] [dest] - Copy file/directory
  mv [src] [dest] - Move file/directory
  cat [file]   - Display file content
  rename [old] [new] - Rename file
  touch [file] - Create empty file or update access time
  tail [file] [N] - Show last N lines (default 10)
  head [file] [N] - Show first N lines (default 10)
  wc [file]    - Count lines, words, bytes
  sort [file]  - Sort file lines
  zip [file]   - Create ZIP archive
  unzip [archive] - Extract ZIP archive
  size [file]  - Show file size
  tree         - Display directory tree
  edit [file]  - Edit file

🛠 System commands:
  ps           - List processes
  sysinfo      - System information
  about        - About PyShell
  env          - Environment variables
  setenv [key] [value] - Set environment variable
  time         - Current time
  clear        - Clear screen
  history      - Command history
  which [command] - Show path to executable

⚙ Utilities:
  echo [text]  - Print text
  find [pattern] - Find file
  grep [text] [file] - Search text in file
  calc [expression] - Calculator

Other:
  help         - Show this help
  exit         - Exit
"""
        return help_text, COLORS["info"]

    def show_about(self, args):
        about_text = f"""
GhostDEV's PyShell is a custom shell for executing commands with Graphical User Interface
        
Some information about PyShell:
Current version: {AppInfo.app_version} ({AppInfo.app_version_state})
Version year: {AppInfo.app_version_year}
Developer: {AppInfo.app_dev}
        
Changelog:
* Added good GUI
* Added new commands
* "Changelog" command was deleted
        
!!! The program may contain some bugs and errors. If you notice any errors, please submit an issue report to the PyShell repository. !!!
        
Thank you for using {AppInfo.app_name}! <3
        """
        
        return about_text, COLORS["command"]
        
    def list_dir(self, args):
        path = args[0] if args else self.current_dir
        try:
            items = os.listdir(path)
            output_lines = [f"Contents of {path}:"]
            for item in items:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    output_lines.append(f"  {GLYPHS['folder']} {item}/")
                else:
                    size = os.path.getsize(full_path)
                    output_lines.append(f"  {GLYPHS['file']} {item} ({size} bytes)")
            return "\n".join(output_lines), COLORS["output"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def change_dir(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify path", COLORS["error"]

        path = args[0]
        try:
            if path == "..":
                os.chdir("..")
            elif path == "~":
                os.chdir(os.path.expanduser("~"))
            else:
                os.chdir(path)
            self.current_dir = os.getcwd()
            self.update_prompt()
            return f"{GLYPHS['folder']} Current directory: {self.current_dir}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def print_work_dir(self, args):
        return f"{GLYPHS['folder']} Current directory: {self.current_dir}", COLORS["info"]

    def make_dir(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify directory name", COLORS["error"]
        dir_name = args[0]
        try:
            os.makedirs(dir_name, exist_ok=True)
            return f"{GLYPHS['success']} Directory created: {dir_name}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def remove_dir(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify directory name", COLORS["error"]
        dir_name = args[0]
        try:
            shutil.rmtree(dir_name)
            return f"{GLYPHS['success']} Directory removed: {dir_name}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def remove_file(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        file_name = args[0]
        try:
            os.remove(file_name)
            return f"{GLYPHS['success']} File removed: {file_name}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def copy_file(self, args):
        if len(args) < 2:
            return f"{GLYPHS['error']} Specify source file and destination", COLORS["error"]
        src, dest = args[0], args[1]
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
            return f"{GLYPHS['success']} Copied: {src} -> {dest}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def move_file(self, args):
        if len(args) < 2:
            return f"{GLYPHS['error']} Specify source file and destination", COLORS["error"]
        src, dest = args[0], args[1]
        try:
            shutil.move(src, dest)
            return f"{GLYPHS['success']} Moved: {src} -> {dest}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def cat_file(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        file_name = args[0]
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                content = f.read()
            return f"{GLYPHS['file']} Contents of file {file_name}:\n{content}", COLORS["output"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def echo_text(self, args):
        return " ".join(args), COLORS["output"]

    def clear_screen(self, args=None):
        self.terminal.delete("1.0", END)
        self.insert_prompt()
        return ""

    def exit_shell(self, args=None):
        self.destroy()
        return ""

    def list_processes(self, args):
        try:
            if platform.system() == "Windows":
                output = subprocess.check_output("tasklist", shell=True, encoding="cp866")
            else:
                output = subprocess.check_output("ps aux", shell=True, encoding="utf-8")
            return f"Running processes:\n{output}", COLORS["output"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def system_info(self, args):
        info = f"""
System Information:
  System: {platform.system()} {platform.release()}
  Processor: {platform.processor()}
  Architecture: {platform.architecture()[0]}
  User: {self.username}
  Working directory: {self.current_dir}
  Start time: {self.session_start}
"""
        return info, COLORS["info"]

    def find_files(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify search pattern", COLORS["error"]
        pattern = args[0]
        found = False
        output = []
        for root, dirs, files in os.walk(self.current_dir):
            for name in files + dirs:
                if pattern.lower() in name.lower():
                    output.append(os.path.join(root, name))
                    found = True
        if not found:
            return f"{GLYPHS['warning']} No files found", COLORS["warning"]
        else:
            return f"{GLYPHS['search']} Found files:\n" + "\n".join(output), COLORS["info"]

    def file_size(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        file_name = args[0]
        try:
            size = os.path.getsize(file_name)
            return f"{GLYPHS['file']} File size: {size} bytes ({size/1024:.2f} KB)", COLORS["info"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def show_time(self, args):
        now = datetime.datetime.now()
        return f"{GLYPHS['time']} Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}", COLORS["info"]

    def show_tree(self, args):
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["tree", self.current_dir], capture_output=True, text=True, encoding="cp866")
            else:
                result = subprocess.run(["tree", self.current_dir], capture_output=True, text=True, encoding="utf-8")
            if result.stdout:
                return result.stdout, COLORS["output"]
            else:
                return f"Directory tree:\n{result.stderr}", COLORS["warning"]
        except:
            return f"{GLYPHS['warning']} 'tree' command not supported on your system", COLORS["warning"]

    def rename_file(self, args):
        if len(args) < 2:
            return f"{GLYPHS['error']} Specify old and new file names", COLORS["error"]
        old_name, new_name = args[0], args[1]
        try:
            os.rename(old_name, new_name)
            return f"{GLYPHS['success']} File renamed: {old_name} -> {new_name}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def grep_text(self, args):
        if len(args) < 2:
            return f"{GLYPHS['error']} Specify text and file name", COLORS["error"]
        text, file_name = args[0], args[1]
        try:
            output = []
            with open(file_name, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if text in line:
                        output.append(f"Line {i+1}: {line.strip()}")
            if output:
                return f"{GLYPHS['search']} Matches found in {file_name}:\n" + "\n".join(output), COLORS["info"]
            else:
                return f"{GLYPHS['warning']} No matches found", COLORS["warning"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def zip_file(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify file/directory", COLORS["error"]
        source = args[0]
        archive = source + ".zip"
        try:
            shutil.make_archive(source, 'zip', os.path.dirname(source), os.path.basename(source))
            return f"{GLYPHS['success']} Archive created: {archive}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def unzip_file(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify archive", COLORS["error"]
        archive = args[0]
        try:
            extract_dir = os.path.splitext(archive)[0]
            shutil.unpack_archive(archive, extract_dir)
            return f"{GLYPHS['success']} Archive extracted to: {extract_dir}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def show_env(self, args):
        output = []
        for key, value in os.environ.items():
            output.append(f"{key}={value}")
        return "Environment variables:\n" + "\n".join(output), COLORS["output"]

    def set_env(self, args):
        if len(args) < 2:
            return f"{GLYPHS['error']} Specify key and value", COLORS["error"]
        key, value = args[0], args[1]
        os.environ[key] = value
        return f"{GLYPHS['success']} Set: {key}={value}", COLORS["success"]

    def show_history(self, args):
        output = []
        for i, cmd in enumerate(self.command_history):
            output.append(f"{i+1}: {cmd}")
        return "Command history:\n" + "\n".join(output), COLORS["info"]

    def calculator(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify expression (example: 2+2)", COLORS["error"]
        try:
            expression = " ".join(args)
            result = eval(expression)
            return f"{GLYPHS['calc']} Result: {result}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Calculation error: {str(e)}", COLORS["error"]

    def edit_file(self, args):
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        filename = args[0]
        try:
            threading.Thread(target=self.open_editor, args=(filename,), daemon=True).start()
            return f"{GLYPHS['edit']} Editor launched for file: {filename}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def open_editor(self, filename):
        editor = TextEditorWindow(self, filename)
        editor.grab_set()
        self.wait_window(editor)

    # New commands
    def touch_file(self, args):
        """Create an empty file or update access time"""
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        filename = args[0]
        try:
            with open(filename, 'a'):
                os.utime(filename, None)
            return f"{GLYPHS['success']} File created/updated: {filename}", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def tail_file(self, args):
        """Show last N lines"""
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        filename = args[0]
        n = 10
        if len(args) > 1:
            try:
                n = int(args[1])
            except:
                pass
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            tail = lines[-n:] if n <= len(lines) else lines
            return f"{GLYPHS['file']} Last {n} lines of file {filename}:\n" + "".join(tail), COLORS["output"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def head_file(self, args):
        """Show first N lines"""
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        filename = args[0]
        n = 10
        if len(args) > 1:
            try:
                n = int(args[1])
            except:
                pass
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            head = lines[:n]
            return f"{GLYPHS['file']} First {n} lines of file {filename}:\n" + "".join(head), COLORS["output"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def word_count(self, args):
        """Count lines, words, bytes"""
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        filename = args[0]
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            lines = content.count('\n')
            words = len(content.split())
            bytes = len(content.encode('utf-8'))
            return f"{GLYPHS['file']} {filename}: {lines} lines, {words} words, {bytes} bytes", COLORS["output"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def sort_file(self, args):
        """Sort file lines"""
        if not args:
            return f"{GLYPHS['error']} Specify file name", COLORS["error"]
        filename = args[0]
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            lines.sort()
            with open(filename, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return f"{GLYPHS['success']} File {filename} sorted", COLORS["success"]
        except Exception as e:
            return f"{GLYPHS['error']} Error: {str(e)}", COLORS["error"]

    def which_command(self, args):
        """Show path to executable"""
        if not args:
            return f"{GLYPHS['error']} Specify command", COLORS["error"]
        cmd = args[0]
        # Check in PATH
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for d in path_dirs:
            full_path = os.path.join(d, cmd)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return f"{GLYPHS['search']} {cmd} -> {full_path}", COLORS["info"]
            # On Windows add .exe etc.
            if platform.system() == "Windows":
                for ext in ['.exe', '.bat', '.cmd']:
                    full_path_ext = full_path + ext
                    if os.path.isfile(full_path_ext) and os.access(full_path_ext, os.X_OK):
                        return f"{GLYPHS['search']} {cmd} -> {full_path_ext}", COLORS["info"]
        return f"{GLYPHS['warning']} Command {cmd} not found in PATH", COLORS["warning"]

    def execute_system_command(self, command):
        """Execute a system command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.stdout:
                return result.stdout, COLORS["output"]
            if result.stderr:
                return f"{result.stderr}", COLORS["error"]
            return ""
        except Exception as e:
            return f"{GLYPHS['error']} Execution error: {str(e)}", COLORS["error"]

if __name__ == "__main__":
    app = TerminalApp()
    app.mainloop()
