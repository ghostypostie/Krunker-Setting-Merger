#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Krunker Settings Keybinds (Controls) Extractor & Merger

This Windows-friendly Tkinter app helps you:
- Extract only the `controls` section (keybinds) from any Krunker settings JSON.
- Merge those keybinds into another settings JSON while preserving all other settings.

Usage from source:
  python krunker_merger.py

Build a standalone .exe (see README.md for details) using PyInstaller.
"""

import json
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Krunker Settings Keybinds Merger"


def load_json_from_text(text: str):
    text = text.strip()
    if not text:
        raise ValueError("No JSON text provided.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Attempt to fix common issues: smart quotes, trailing commas
        raise ValueError(f"Invalid JSON. Details: {e}")


def extract_controls(settings_obj):
    if not isinstance(settings_obj, dict):
        raise ValueError("Settings JSON must be an object (dictionary).")
    if "controls" not in settings_obj:
        raise KeyError("This settings JSON does not contain a 'controls' section.")
    return {"controls": settings_obj["controls"]}


def merge_controls(source_controls_obj, target_settings_obj):
    """
    source_controls_obj: {"controls": {...}}
    target_settings_obj: full settings dict
    Returns a new dict: target_settings with controls replaced by source controls
    """
    if "controls" not in source_controls_obj:
        raise KeyError("Source controls object must contain 'controls'.")
    merged = dict(target_settings_obj)  # shallow copy is fine for replacement
    merged["controls"] = source_controls_obj["controls"]
    return merged


class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=0)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)

        self._dark_mode = tk.BooleanVar(value=False)

        # Build the UI
        self._build_menu()
        self._build_toolbar()
        self._build_tabs()
        self._build_statusbar()
        self._apply_theme()  # initial theme

    def _build_menu(self):
        menubar = tk.Menu(self.master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Source...", accelerator="Ctrl+O", command=self.open_src_file)
        file_menu.add_command(label="Open Target...", accelerator="Ctrl+Shift+O", command=self.open_tgt_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save Result As...", accelerator="Ctrl+S", command=self.save_result)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Paste Source", accelerator="Ctrl+V", command=self.paste_src)
        edit_menu.add_command(label="Paste Target", accelerator="Ctrl+Shift+V", command=self.paste_tgt)
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy Result", accelerator="Ctrl+C", command=self.copy_result)
        edit_menu.add_command(label="Clear All", command=self.clear_all)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        actions_menu = tk.Menu(menubar, tearoff=0)
        actions_menu.add_command(label="Extract Controls", accelerator="Ctrl+E", command=self.extract_src_controls)
        actions_menu.add_command(label="Merge Controls", accelerator="Ctrl+M", command=self.merge_into_target)
        actions_menu.add_checkbutton(label="Dark Mode", onvalue=True, offvalue=False, variable=self._dark_mode, command=self._apply_theme)
        menubar.add_cascade(label="Actions", menu=actions_menu)

        self.master.config(menu=menubar)

        # Shortcuts
        self.master.bind_all("<Control-o>", lambda e: self.open_src_file())
        self.master.bind_all("<Control-O>", lambda e: self.open_src_file())
        self.master.bind_all("<Control-E>", lambda e: self.extract_src_controls())
        self.master.bind_all("<Control-e>", lambda e: self.extract_src_controls())
        self.master.bind_all("<Control-m>", lambda e: self.merge_into_target())
        self.master.bind_all("<Control-M>", lambda e: self.merge_into_target())
        self.master.bind_all("<Control-s>", lambda e: self.save_result())
        self.master.bind_all("<Control-S>", lambda e: self.save_result())
        # Target open/paste with Shift
        self.master.bind_all("<Control-Shift-O>", lambda e: self.open_tgt_file())
        self.master.bind_all("<Control-Shift-V>", lambda e: self.paste_tgt())

    def _build_toolbar(self):
        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(toolbar, text=APP_TITLE, font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)

        btns = ttk.Frame(toolbar)
        btns.pack(side=tk.RIGHT)
        ttk.Button(btns, text="Extract Controls", command=self.extract_src_controls).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="Merge Controls →", command=self.merge_into_target).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="Copy Result", command=self.copy_result).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="Save Result", command=self.save_result).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Checkbutton(btns, text="Dark Mode", variable=self._dark_mode, command=self._apply_theme).pack(side=tk.LEFT)

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- Tab 1: Merge ---
        merge_tab = ttk.Frame(self.notebook)
        self.notebook.add(merge_tab, text="Merge")

        # Main split: vertical (top editors, bottom result)
        main_panes = ttk.Panedwindow(merge_tab, orient=tk.VERTICAL)
        main_panes.pack(fill=tk.BOTH, expand=True)

        # Top split: source | target
        top_panes = ttk.Panedwindow(main_panes, orient=tk.HORIZONTAL)
        main_panes.add(top_panes, weight=3)

        # Source frame
        src_frame = ttk.LabelFrame(top_panes, text="1) Source settings (has desired keybinds)")
        src_frame.columnconfigure(0, weight=1)
        src_frame.rowconfigure(1, weight=1)
        top_panes.add(src_frame, weight=1)

        src_btns = ttk.Frame(src_frame)
        src_btns.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))
        ttk.Button(src_btns, text="Open JSON...", command=self.open_src_file).pack(side=tk.LEFT)
        ttk.Button(src_btns, text="Paste", command=self.paste_src).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(src_btns, text="Extract", command=self.extract_src_controls).pack(side=tk.LEFT, padx=(6, 0))

        self.src_text = tk.Text(src_frame, wrap="none", height=18, undo=True)
        self.src_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self._add_text_scrollbars(src_frame, self.src_text)

        # Target frame
        tgt_frame = ttk.LabelFrame(top_panes, text="2) Target settings (to receive keybinds)")
        tgt_frame.columnconfigure(0, weight=1)
        tgt_frame.rowconfigure(1, weight=1)
        top_panes.add(tgt_frame, weight=1)

        tgt_btns = ttk.Frame(tgt_frame)
        tgt_btns.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))
        ttk.Button(tgt_btns, text="Open JSON...", command=self.open_tgt_file).pack(side=tk.LEFT)
        ttk.Button(tgt_btns, text="Paste", command=self.paste_tgt).pack(side=tk.LEFT, padx=(6, 0))
        ttk.Button(tgt_btns, text="Merge →", command=self.merge_into_target).pack(side=tk.LEFT, padx=(6, 0))

        self.tgt_text = tk.Text(tgt_frame, wrap="none", height=18, undo=True)
        self.tgt_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self._add_text_scrollbars(tgt_frame, self.tgt_text)

        # Output frame
        out_frame = ttk.LabelFrame(main_panes, text="3) Result (merged or controls-only)")
        out_frame.columnconfigure(0, weight=1)
        out_frame.rowconfigure(0, weight=1)
        main_panes.add(out_frame, weight=2)

        self.out_text = tk.Text(out_frame, wrap="none", height=12, undo=True)
        self.out_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 10))
        self._add_text_scrollbars(out_frame, self.out_text)

        # --- Tab 2: Validate ---
        validate_tab = ttk.Frame(self.notebook)
        self.notebook.add(validate_tab, text="Validate")

        validate_tab.columnconfigure(0, weight=1)
        validate_tab.rowconfigure(1, weight=1)

        vbar = ttk.Frame(validate_tab, padding=(10, 10))
        vbar.grid(row=0, column=0, sticky="ew")
        ttk.Label(vbar, text="Quickly validate and pretty‑print JSON.").pack(side=tk.LEFT)
        ttk.Button(vbar, text="Validate Source", command=self._validate_source).pack(side=tk.LEFT, padx=6)
        ttk.Button(vbar, text="Validate Target", command=self._validate_target).pack(side=tk.LEFT)

        vpanes = ttk.Panedwindow(validate_tab, orient=tk.HORIZONTAL)
        vpanes.grid(row=1, column=0, sticky="nsew")

        vleft = ttk.LabelFrame(vpanes, text="Source JSON")
        vleft.columnconfigure(0, weight=1)
        vleft.rowconfigure(0, weight=1)
        vpanes.add(vleft, weight=1)
        self.v_src_text = tk.Text(vleft, wrap="none", undo=True)
        self.v_src_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self._add_text_scrollbars(vleft, self.v_src_text)

        vright = ttk.LabelFrame(vpanes, text="Target JSON")
        vright.columnconfigure(0, weight=1)
        vright.rowconfigure(0, weight=1)
        vpanes.add(vright, weight=1)
        self.v_tgt_text = tk.Text(vright, wrap="none", undo=True)
        self.v_tgt_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self._add_text_scrollbars(vright, self.v_tgt_text)

        # --- Tab 3: About ---
        about_tab = ttk.Frame(self.notebook)
        self.notebook.add(about_tab, text="About")

        about = ttk.Label(
            about_tab,
            padding=20,
            justify=tk.LEFT,
            text=(
                f"{APP_TITLE}\n\n"
                "A simple desktop utility to extract only the 'controls' (keybinds) from a Krunker settings JSON "
                "and merge them into another settings JSON without changing anything else.\n\n"
                "Tips:\n"
                "- Use the Merge tab for your daily workflow.\n"
                "- The Validate tab helps check JSON and pretty‑print it.\n"
                "- Toggle Dark Mode from the toolbar or Actions menu.\n\n"
                "All processing happens locally on your machine."
            ),
        )
        about.pack(anchor="nw")

    # Validation helpers for the Validate tab
    def _validate_json_text(self, text_widget: tk.Text, name: str):
        txt = text_widget.get("1.0", tk.END).strip()
        if not txt:
            self._set_status(f"{name}: empty")
            return
        try:
            obj = json.loads(txt)
            pretty = json.dumps(obj, indent=2, ensure_ascii=False)
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", pretty)
            self._set_status(f"{name}: valid JSON ✓")
        except Exception as e:
            self._set_status(f"{name}: invalid JSON — {e}")

    def _validate_source(self):
        self._validate_json_text(self.v_src_text, "Source")

    def _validate_target(self):
        self._validate_json_text(self.v_tgt_text, "Target")

    def _build_statusbar(self):
        self.status = tk.StringVar(value="Ready")
        bar = ttk.Frame(self, padding=(10, 4))
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(bar, textvariable=self.status).pack(side=tk.LEFT)

    def _set_status(self, text: str):
        self.status.set(text)

    def _add_text_scrollbars(self, parent, text_widget):
        xscroll = ttk.Scrollbar(parent, orient="horizontal", command=text_widget.xview)
        yscroll = ttk.Scrollbar(parent, orient="vertical", command=text_widget.yview)
        text_widget.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set, font=("Consolas", 10), insertwidth=2)
        yscroll.grid(row=1, column=1, sticky="ns")
        xscroll.grid(row=2, column=0, sticky="ew")

    def _apply_theme(self):
        try:
            style = ttk.Style()
            if sys.platform.startswith("win"):
                style.theme_use("vista")
        except Exception:
            pass

        # Colors for dark/light
        if self._dark_mode.get():
            bg = "#1e1e1e"
            fg = "#e5e5e5"
            sel = "#264f78"
        else:
            bg = "#ffffff"
            fg = "#000000"
            sel = "#cde6ff"

        for text_widget in getattr(self, 'src_text', []), getattr(self, 'tgt_text', []), getattr(self, 'out_text', []):
            if isinstance(text_widget, tk.Text):
                text_widget.configure(bg=bg, fg=fg, insertbackground=fg, selectbackground=sel)

    # File/Clipboard helpers
    def open_src_file(self):
        path = filedialog.askopenfilename(title="Open Source Settings JSON", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.src_text.delete("1.0", tk.END)
            self.src_text.insert("1.0", data)
            self._set_status(f"Loaded source: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")

    def open_tgt_file(self):
        path = filedialog.askopenfilename(title="Open Target Settings JSON", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.tgt_text.delete("1.0", tk.END)
            self.tgt_text.insert("1.0", data)
            self._set_status(f"Loaded target: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{e}")

    def paste_src(self):
        try:
            self.src_text.delete("1.0", tk.END)
            self.src_text.insert("1.0", self.master.clipboard_get())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste from clipboard:\n{e}")

    def paste_tgt(self):
        try:
            self.tgt_text.delete("1.0", tk.END)
            self.tgt_text.insert("1.0", self.master.clipboard_get())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to paste from clipboard:\n{e}")

    def copy_result(self):
        text = self.out_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "Nothing to copy.")
            return
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        self._set_status("Result JSON copied to clipboard.")

    def save_result(self):
        text = self.out_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Info", "Nothing to save.")
            return
        path = filedialog.asksaveasfilename(title="Save Result JSON", defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._set_status(f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def clear_all(self):
        for widget in (self.src_text, self.tgt_text, self.out_text):
            widget.delete("1.0", tk.END)
        self._set_status("Cleared.")

    # Core actions
    def extract_src_controls(self):
        try:
            src_obj = load_json_from_text(self.src_text.get("1.0", tk.END))
            controls_only = extract_controls(src_obj)
            pretty = json.dumps(controls_only, indent=2, ensure_ascii=False)
            self.out_text.delete("1.0", tk.END)
            self.out_text.insert("1.0", pretty)
            self._set_status("Extracted controls from source.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def merge_into_target(self):
        try:
            src_obj = load_json_from_text(self.src_text.get("1.0", tk.END))
            if "controls" not in src_obj:
                # Maybe user already extracted controls-only into output; try from output first
                try:
                    src_obj = load_json_from_text(self.out_text.get("1.0", tk.END))
                except Exception:
                    pass
            if "controls" not in src_obj:
                raise KeyError("Source must contain 'controls'. Use 'Extract Controls' first if needed.")

            tgt_obj = load_json_from_text(self.tgt_text.get("1.0", tk.END))
            merged = merge_controls(src_obj, tgt_obj)
            pretty = json.dumps(merged, indent=2, ensure_ascii=False)
            self.out_text.delete("1.0", tk.END)
            self.out_text.insert("1.0", pretty)
            self._set_status("Merged controls into target.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


def main():
    root = tk.Tk()
    root.title(APP_TITLE)
    # Better default window size
    root.geometry("1200x800")
    # Use native-looking theme
    try:
        style = ttk.Style()
        if sys.platform.startswith("win"):
            style.theme_use("vista")
    except Exception:
        pass

    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
