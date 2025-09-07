# Krunker Settings Keybinds (Controls) Extractor & Merger

This small Windows-friendly Python app lets you:

- Extract only the `controls` (keybinds) from any Krunker settings JSON.
- Merge those `controls` into another settings JSON while preserving all other settings.

The app works fully offline and never uploads your settings anywhere.

## Run from Source

Requirements:
- Python 3.8+ on Windows

Steps:
1. Double-click `krunker_merger.py` if Python is associated with `.py` files, or run:
   ```bash
   python krunker_merger.py
   ```
2. In the app:
   - Paste or open your source settings JSON on the left (the one with the keybinds you want).
   - Click `Extract Controls` to produce controls-only JSON in the result pane.
   - Paste or open your target settings JSON on the right (the settings you want to keep but with your controls).
   - Click `Merge Controls →` to produce the merged result in the result pane.
   - Copy or Save the result.

## Build a Single .exe (No Python Needed to Run)

1. Install PyInstaller (one-time):
   ```bash
   pip install --upgrade pyinstaller
   ```
2. Build the executable from this folder:
   ```bash
   pyinstaller --noconfirm --onefile --windowed --name "KrunkerKeybindsMerger" krunker_merger.py
   ```
3. Your `.exe` will be in the `dist/` folder as `KrunkerKeybindsMerger.exe`.

Notes:
- `--windowed` hides the console window.
- If SmartScreen warns, click `More info` → `Run anyway` (since it's locally built and unsigned).

## FAQ

- Q: My JSON fails to load.
  - A: Ensure you pasted the full export from Krunker. The app expects valid JSON. If you edited it manually, double-check commas and quotes.

- Q: Can I feed controls-only JSON as the source?
  - A: Yes. If the left side contains a full settings object, click `Extract Controls` first. Otherwise, you can paste a `{ "controls": { ... } }` object directly and click `Merge Controls →`.

- Q: What exactly gets changed during merge?
  - A: Only the `controls` property is replaced in the target JSON. Everything else is preserved.

## Privacy

This tool does not upload any data. All processing is local on your machine.
