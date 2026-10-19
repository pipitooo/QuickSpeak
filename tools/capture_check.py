"""Run against a synthetic selection already made in the foreground app."""
import multiprocessing
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == '__main__':
    multiprocessing.freeze_support()
    from quickspeak.selection import capture_selection, clipboard_selection, snapshot_clipboard, u32
    import win32gui
    mode = sys.argv[1] if len(sys.argv) > 1 else 'uia'
    before = u32.GetClipboardSequenceNumber()
    start = time.perf_counter()
    if mode == 'fallback':
        snapshot, _ = snapshot_clipboard()
        text, method = clipboard_selection(win32gui.GetForegroundWindow()), 'Clipboard fallback'
        after_snapshot, _ = snapshot_clipboard()
        restored = snapshot == after_snapshot
    else:
        text, method = capture_selection(win32gui.GetForegroundWindow())
        restored = before == u32.GetClipboardSequenceNumber()
    print(json.dumps({'text': text, 'method': method, 'elapsed_s': round(time.perf_counter() - start, 3),
                      'clipboard_preserved': restored}, ensure_ascii=True))
