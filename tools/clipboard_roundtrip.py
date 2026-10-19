"""Integration test on a synthetic selection; restore user's initial clipboard."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quickspeak.selection import *

original, sequence = snapshot_clipboard()
try:
    html = cb.RegisterClipboardFormat('HTML Format')
    rtf = cb.RegisterClipboardFormat('Rich Text Format')
    expected = [(13, 'QuickSpeak clipboard sentinel — café'), (html, b'<b>Sentinel</b>\0'), (rtf, b'{\\rtf1 Sentinel}\0')]
    open_clipboard()
    try:
        cb.EmptyClipboard()
        for fmt, value in expected:
            cb.SetClipboardData(fmt, value)
    finally:
        cb.CloseClipboard()
    baseline, _ = snapshot_clipboard()
    selected = clipboard_selection(win32gui.GetForegroundWindow())
    after, _ = snapshot_clipboard()
    import json
    print(json.dumps({'selection': selected, 'restored_all_test_formats': baseline == after, 'format_ids': [x[0] for x in after]}, ensure_ascii=True))
finally:
    open_clipboard()
    try:
        cb.EmptyClipboard()
        for fmt, value in original:
            cb.SetClipboardData(fmt, value)
    finally:
        cb.CloseClipboard()
