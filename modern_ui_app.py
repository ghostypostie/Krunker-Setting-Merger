#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Next‑gen UI launcher for Krunker Settings Keybinds Merger using pywebview.
- Presents a modern HTML/CSS/JS front end with glassmorphism and animations
- Exposes Python APIs for JSON operations and file dialog I/O

Run:
  python modern_ui_app.py

Build EXE (example):
  pyinstaller --noconfirm --onefile --windowed --name "KrunkerKeybindsMergerNext" modern_ui_app.py

Dependencies:
  pip install pywebview
"""

import json
import os
import sys
import webview
from tkinter import filedialog, Tk

# Reuse logic from krunker_merger
from krunker_merger import extract_controls, merge_controls

APP_TITLE = "Krunker Keybinds Merger"

# Resolve UI path both in dev and when frozen by PyInstaller
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running from PyInstaller bundle
    UI_DIR = os.path.join(sys._MEIPASS, 'ui')  # type: ignore[attr-defined]
else:
    UI_DIR = os.path.join(BASE_DIR, 'ui')
INDEX_PATH = os.path.join(UI_DIR, 'index.html')


class API:
    def __init__(self):
        # Hidden Tk root for native file dialogs
        self._tk = Tk()
        self._tk.withdraw()

    # File dialogs
    def open_file(self):
        path = filedialog.askopenfilename(title="Open Settings JSON", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not path:
            return {"path": None, "content": None}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"path": path, "content": content}
        except Exception as e:
            return {"error": str(e)}

    def save_file(self, text: str):
        path = filedialog.asksaveasfilename(title="Save Result JSON", defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if not path:
            return {"path": None}
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
            return {"path": path}
        except Exception as e:
            return {"error": str(e)}

    # JSON helpers
    def pretty(self, text: str):
        try:
            obj = json.loads(text)
            return {"ok": True, "text": json.dumps(obj, indent=2, ensure_ascii=False)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def validate(self, text: str):
        try:
            json.loads(text)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def extract_controls(self, source_text: str):
        try:
            src = json.loads(source_text)
            controls_only = extract_controls(src)
            return {"ok": True, "text": json.dumps(controls_only, indent=2, ensure_ascii=False)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def merge(self, source_controls_text: str, target_text: str):
        try:
            src = json.loads(source_controls_text)
            tgt = json.loads(target_text)
            merged = merge_controls(src, tgt)
            # Return unpretty (minified) JSON for result as requested
            return {"ok": True, "text": json.dumps(merged, separators=(',', ':'), ensure_ascii=False)}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def start():
    # Ensure UI dir exists
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(f"UI index not found: {INDEX_PATH}. If running a bundled EXE, ensure the 'ui' folder is added via PyInstaller --add-data.")

    api = API()
    webview.create_window(APP_TITLE, INDEX_PATH, width=1200, height=800, resizable=True, confirm_close=False, easy_drag=False, js_api=api)

    def on_start():
        try:
            w = webview.windows[0]
            w.maximize()
        except Exception:
            pass

    webview.start(http_server=True, gui='edgechromium' if sys.platform.startswith('win') else None, func=on_start, debug=False)


if __name__ == '__main__':
    start()
